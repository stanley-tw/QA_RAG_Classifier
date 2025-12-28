from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

from src.config import AppConfig
from src.db.candidate_repo import insert_candidate
from src.db.content_repo import (
    has_content_blocks_for_pdf,
    insert_content_blocks,
    list_content_blocks_by_pdf,
)
from src.db.domain_repo import list_domain_aliases, list_domain_sources, list_domains
from src.db.embedding_repo import (
    insert_candidate_embedding,
    insert_domain_embedding,
)
from src.db.review_repo import list_rejected_pairs
from src.db.repo import clear_derived_tables
from src.db.schema import create_schema
from src.pipeline.artifact import write_artifact_bundle
from src.pipeline.artifact_versioning import next_bundle_dir
from src.pipeline.candidates import ContentBlock, DomainCandidate, extract_candidates
from src.pipeline.embedding import AzureOpenAIEmbedder, serialize_vector
from src.pipeline.ingest import parse_document
from src.pipeline.label_index import build_label_index
from src.pipeline.markdown_parser import parse_markdown
from src.pipeline.merge import merge_candidates
from src.pipeline.merge_persist import persist_merge_results
from src.pipeline.representation import BlockScore, select_top_k_blocks
from src.pipeline.similarity import generate_candidate_pairs, similarity_pairs_for_mode


def run_pipeline(
    config: AppConfig,
    progress_cb: Callable[[str, float], None] | None = None,
) -> bool:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
    conn = sqlite3.connect(config.db_path)
    try:
        create_schema(conn)
        pdfs = _list_pdfs(conn)
        if not pdfs:
            logger.info("No PDFs found to process.")
            return False
        pdfs_to_process = _select_pdfs_to_process(conn, pdfs, config.skip_processed_pdfs)
        if not pdfs_to_process:
            logger.info("No unprocessed PDFs to process.")
            return False
        _report(progress_cb, "Preparing pipeline", 0.05)
        clear_derived_tables(conn)

        Path(config.rag_output_dir).mkdir(parents=True, exist_ok=True)
        for pdf in pdfs_to_process:
            logger.info("Parsing PDF: %s", pdf["file_path"])
            if not has_content_blocks_for_pdf(conn, pdf["pdf_id"]):
                blocks = _parse_pdf_to_blocks(
                    pdf_path=pdf["file_path"],
                    pdf_id=pdf["pdf_id"],
                    output_dir=config.rag_output_dir,
                    parser_name=config.rag_parser,
                    parse_method=config.rag_parse_method,
                )
                insert_content_blocks(conn, blocks)
        _report(progress_cb, "Extracting candidates", 0.25)

        candidates = _extract_and_store_candidates(
            conn, pdf_ids={pdf["pdf_id"] for pdf in pdfs_to_process}
        )
        if not candidates:
            logger.info("No candidates extracted.")
            return False

        embedding_model = config.embedding_model
        embedding_dim = config.embedding_dimensions.get(embedding_model, 1536)
        embedder = AzureOpenAIEmbedder(
            model_name=embedding_model,
            max_tokens=config.max_tokens_per_embed,
            approx_enabled=config.tokenization_fallback_approx_enabled,
        )

        _report(progress_cb, "Embedding candidates", 0.4)
        name_only_texts = [c.candidate_name for c in candidates]
        name_plus_texts = [
            f"{c.candidate_name}\n{c.representative_text}" for c in candidates
        ]
        name_only_embeddings = embedder.embed_texts(conn, name_only_texts)
        name_plus_embeddings = embedder.embed_texts(conn, name_plus_texts)

        candidate_ids = [c.candidate_id for c in candidates]
        embeddings_by_id_name = dict(
            zip(candidate_ids, name_only_embeddings.vectors, strict=False)
        )
        embeddings_by_id_plus = dict(
            zip(candidate_ids, name_plus_embeddings.vectors, strict=False)
        )

        for candidate, vector, token_count in zip(
            candidates,
            name_plus_embeddings.vectors,
            name_plus_embeddings.token_counts,
            strict=False,
        ):
            insert_candidate_embedding(
                conn,
                candidate_id=candidate.candidate_id,
                model_name=embedding_model,
                vector=serialize_vector(vector),
                token_count=token_count,
                tokenization_mode=name_plus_embeddings.tokenization_mode,
            )

        normalized = {c.candidate_id: c.normalized_name for c in candidates}
        pairs = generate_candidate_pairs(candidate_ids, normalized)
        similarities = []
        similarities += similarity_pairs_for_mode(
            pairs, embeddings_by_id_name, "name_only"
        )
        similarities += similarity_pairs_for_mode(
            pairs, embeddings_by_id_plus, "name_plus_summary"
        )

        rejected_pairs = list_rejected_pairs(conn)
        thresholds_by_mode = {
            "name_only": (
                config.merge_threshold_name_only,
                config.review_threshold_name_only,
            ),
            "name_plus_summary": (
                config.merge_threshold_name_plus_summary,
                config.review_threshold_name_plus_summary,
            ),
        }
        _report(progress_cb, "Merging candidates", 0.6)
        merge_result = merge_candidates(
            similarities=similarities,
            thresholds_by_mode=thresholds_by_mode,
            rejected_pairs=rejected_pairs,
            items=candidate_ids,
        )

        now = datetime.now(timezone.utc).isoformat()
        review_items = [
            (item.pair[0], item.pair[1], item.similarity, item.reason)
            for item in merge_result.review_items
        ]
        min_review_threshold = min(
            config.review_threshold_name_only,
            config.review_threshold_name_plus_summary,
        )
        persist_merge_results(
            conn=conn,
            clusters=merge_result.clusters,
            candidates={c.candidate_id: c for c in candidates},
            review_items=review_items,
            persist_pairs=merge_result.persist_pairs,
            created_at=now,
            preferred_display_language=config.preferred_display_language,
            min_review_threshold=min_review_threshold,
        )

        domains = _build_domains_payload(conn)
        _report(progress_cb, "Embedding domains", 0.8)
        domain_embeddings = _build_domain_embeddings(
            conn,
            domains=domains,
            candidates={c.candidate_id: c for c in candidates},
            embedder=embedder,
        )
        label_index = build_label_index(
            embedding_model=embedding_model,
            embedding_dimension=embedding_dim,
            domains=domains,
        )
        label_vec = _build_label_vec(label_index, domain_embeddings, embedding_dim)

        bundle_dir = next_bundle_dir(Path(config.artifact_dir))
        bundle_dir.mkdir(parents=True, exist_ok=True)
        write_artifact_bundle(
            output_dir=bundle_dir,
            artifact_version="v1",
            embedding_model=embedding_model,
            embedding_provider="azure_openai",
            embedding_dimension=embedding_dim,
            tokenization_mode=name_plus_embeddings.tokenization_mode,
            tokenization_fallback_allowed=config.tokenization_fallback_approx_enabled,
            generation_config={
                "merge_threshold_name_only": config.merge_threshold_name_only,
                "merge_threshold_name_plus_summary": config.merge_threshold_name_plus_summary,
                "preferred_display_language": config.preferred_display_language,
            },
            domains=domains,
            label_index=label_index,
            label_vec=label_vec,
            domain_repr=[
                {
                    "domain_id": domain_id,
                    "representation_text": text,
                }
                for domain_id, text in domain_embeddings.items()
            ],
        )
        _report(progress_cb, "Artifact bundle written", 1.0)
        return True
    finally:
        conn.close()


def _list_pdfs(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT pdf_id, file_path, checksum, ingested_at FROM pdfs ORDER BY pdf_id;"
    ).fetchall()
    return [dict(row) for row in rows]


def _select_pdfs_to_process(
    conn: sqlite3.Connection,
    pdfs: List[Dict[str, str]],
    skip_processed: bool,
) -> List[Dict[str, str]]:
    if not skip_processed:
        return pdfs
    return [pdf for pdf in pdfs if not has_content_blocks_for_pdf(conn, pdf["pdf_id"])]


def _report(progress_cb: Callable[[str, float], None] | None, message: str, pct: float) -> None:
    if progress_cb:
        progress_cb(message, pct)


def _parse_pdf_to_blocks(
    pdf_path: str,
    pdf_id: str,
    output_dir: str,
    parser_name: str,
    parse_method: str,
) -> List[Dict[str, object]]:
    parsed = parse_document(
        file_path=pdf_path,
        output_dir=output_dir,
        parser_name=parser_name,
        parse_method=parse_method,
    )
    blocks: List[Dict[str, object]] = []
    markdown_blocks = parse_markdown(parsed.markdown) if parsed.markdown else []
    if markdown_blocks:
        for idx, block in enumerate(markdown_blocks):
            blocks.append(
                {
                    "block_id": f"{pdf_id}_b{idx:05d}",
                    "pdf_id": pdf_id,
                    "section_path": block.section_path,
                    "heading_level": block.heading_level,
                    "block_type": block.block_type,
                    "text": block.text,
                    "page_index": 0,
                    "position_index": idx,
                }
            )
        return blocks

    position = 0
    for item in parsed.content_list:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "text":
            continue
        text = item.get("text", "").strip()
        if not text:
            continue
        blocks.append(
            {
                "block_id": f"{pdf_id}_b{position:05d}",
                "pdf_id": pdf_id,
                "section_path": "",
                "heading_level": 0,
                "block_type": "paragraph",
                "text": text,
                "page_index": int(item.get("page_idx", 0)),
                "position_index": position,
            }
        )
        position += 1
    return blocks


def _extract_and_store_candidates(
    conn: sqlite3.Connection, pdf_ids: set[str]
) -> List[DomainCandidate]:
    rows: List[Dict[str, object]] = []
    for pdf_id in sorted(pdf_ids):
        rows.extend(list_content_blocks_by_pdf(conn, pdf_id))
    blocks = [
        ContentBlock(
            block_id=row["block_id"],
            pdf_id=row["pdf_id"],
            section_path=row.get("section_path") or "",
            heading_level=row.get("heading_level") or 0,
            block_type=row.get("block_type") or "paragraph",
            text=row.get("text") or "",
            page_index=row.get("page_index") or 0,
            position_index=row.get("position_index") or 0,
        )
        for row in rows
    ]
    candidates = extract_candidates(blocks)
    conn.execute("DELETE FROM domain_candidates;")
    for candidate in candidates:
        insert_candidate(
            conn,
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.candidate_name,
            normalized_name=candidate.normalized_name,
            source_pdf_id=candidate.source_pdf_id,
            source_block_id=candidate.source_block_id,
            heading_level=candidate.heading_level,
            representative_text=candidate.representative_text,
        )
    return candidates


def _build_domains_payload(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    domains = list_domains(conn)
    aliases = list_domain_aliases(conn)
    sources = list_domain_sources(conn)
    aliases_by_domain: Dict[str, List[str]] = {}
    for alias in aliases:
        aliases_by_domain.setdefault(alias["domain_id"], []).append(alias["alias"])
    sources_by_domain: Dict[str, List[str]] = {}
    for source in sources:
        sources_by_domain.setdefault(source["domain_id"], []).append(source["pdf_id"])
    payload = []
    for domain in domains:
        payload.append(
            {
                "domain_id": domain["domain_id"],
                "display_name": domain["display_name"],
                "aliases": aliases_by_domain.get(domain["domain_id"], []),
                "source_pdfs": sources_by_domain.get(domain["domain_id"], []),
            }
        )
    return payload


def _build_domain_embeddings(
    conn: sqlite3.Connection,
    domains: List[Dict[str, object]],
    candidates: Dict[str, DomainCandidate],
    embedder: AzureOpenAIEmbedder,
) -> Dict[str, List[float]]:
    conn.row_factory = sqlite3.Row
    block_map = conn.execute(
        "SELECT block_id, domain_id FROM block_domain_map ORDER BY block_id;"
    ).fetchall()
    block_by_domain: Dict[str, List[str]] = {}
    for row in block_map:
        block_by_domain.setdefault(row["domain_id"], []).append(row["block_id"])

    domain_texts: List[str] = []
    domain_ids: List[str] = []
    for domain in domains:
        domain_id = domain["domain_id"]
        candidate_ids = block_by_domain.get(domain_id, [])
        blocks = []
        for cid in candidate_ids:
            candidate = candidates.get(cid)
            if candidate:
                blocks.append(
                    BlockScore(
                        block_id=cid,
                        score=float(len(candidate.representative_text)),
                        text=candidate.representative_text,
                    )
                )
        top_blocks = select_top_k_blocks(blocks, k=5)
        text = "\n".join(block.text for block in top_blocks).strip()
        domain_ids.append(domain_id)
        domain_texts.append(text or domain["display_name"])

    embedded = embedder.embed_texts(conn, domain_texts)
    embeddings: Dict[str, List[float]] = {}
    for domain_id, vector, token_count in zip(
        domain_ids, embedded.vectors, embedded.token_counts, strict=False
    ):
        embeddings[domain_id] = vector
        insert_domain_embedding(
            conn,
            domain_id=domain_id,
            model_name=embedder.model_name,
            vector=serialize_vector(vector),
            token_count=token_count,
            tokenization_mode=embedded.tokenization_mode,
        )
    return embeddings


def _build_label_vec(
    label_index: Dict[str, object],
    embeddings: Dict[str, List[float]],
    embedding_dimension: int,
) -> np.ndarray:
    domain_ids = label_index["domain_ids"]
    matrix = np.zeros((len(domain_ids), embedding_dimension), dtype=np.float32)
    for i, domain_id in enumerate(domain_ids):
        vector = embeddings.get(domain_id)
        if vector is None:
            continue
        matrix[i] = np.array(vector, dtype=np.float32)
    return matrix
