from __future__ import annotations

import sqlite3
from typing import Dict, Iterable, List, Set, Tuple

from src.db.domain_repo import (
    insert_block_domain_map,
    insert_domain,
    insert_domain_alias,
    insert_domain_source,
)
from src.db.review_repo import has_review_pair, insert_review_item
from src.pipeline.hash_utils import text_hash
from src.db.similarity_repo import insert_similarity_pairs
from src.pipeline.candidates import DomainCandidate
from src.pipeline.naming import AliasInfo, select_display_name


def persist_merge_results(
    conn: sqlite3.Connection,
    clusters: Iterable[Set[str]],
    candidates: Dict[str, DomainCandidate],
    review_items: Iterable[Tuple[str, str, float, str]],
    persist_pairs: Iterable[Tuple[str, str, float, str]],
    created_at: str,
    preferred_display_language: str,
    min_review_threshold: float,
) -> None:
    _persist_domains(conn, clusters, candidates, created_at, preferred_display_language)
    _persist_review_queue(conn, review_items, created_at)
    _persist_similarity(conn, persist_pairs, min_review_threshold)


def _persist_domains(
    conn: sqlite3.Connection,
    clusters: Iterable[Set[str]],
    candidates: Dict[str, DomainCandidate],
    created_at: str,
    preferred_display_language: str,
) -> None:
    sorted_clusters = sorted(
        (sorted(cluster) for cluster in clusters), key=lambda c: c[0]
    )
    for idx, cluster in enumerate(sorted_clusters, start=1):
        domain_id = f"domain_{idx:03d}"
        alias_infos = [
            AliasInfo(
                alias=candidates[cid].candidate_name,
                source_pdf_id=candidates[cid].source_pdf_id,
                heading_level=candidates[cid].heading_level,
            )
            for cid in cluster
            if cid in candidates
        ]
        display_name = select_display_name(
            alias_infos, preferred_language=preferred_display_language
        )
        insert_domain(conn, domain_id=domain_id, display_name=display_name, created_at=created_at)
        _persist_domain_mappings(conn, domain_id, cluster, candidates)


def _persist_domain_mappings(
    conn: sqlite3.Connection,
    domain_id: str,
    cluster: List[str],
    candidates: Dict[str, DomainCandidate],
) -> None:
    seen_sources: set[str] = set()
    for cid in cluster:
        if cid not in candidates:
            continue
        candidate = candidates[cid]
        insert_domain_alias(
            conn,
            domain_id=domain_id,
            alias=candidate.candidate_name,
            source_pdf_id=candidate.source_pdf_id,
            heading_level=candidate.heading_level,
        )
        insert_block_domain_map(
            conn, block_id=candidate.source_block_id, domain_id=domain_id
        )
        if candidate.source_pdf_id not in seen_sources:
            insert_domain_source(conn, domain_id=domain_id, pdf_id=candidate.source_pdf_id)
            seen_sources.add(candidate.source_pdf_id)


def _persist_review_queue(
    conn: sqlite3.Connection,
    review_items: Iterable[Tuple[str, str, float, str]],
    created_at: str,
) -> None:
    for a, b, similarity, reason in review_items:
        if has_review_pair(conn, a, b):
            continue
        digest = text_hash(f"{a}|{b}")[:10]
        review_id = f"review_{digest}"
        insert_review_item(
            conn,
            review_id=review_id,
            candidate_a_id=a,
            candidate_b_id=b,
            similarity=similarity,
            reason=reason,
            status="pending",
            created_at=created_at,
        )


def _persist_similarity(
    conn: sqlite3.Connection,
    persist_pairs: Iterable[Tuple[str, str, float, str]],
    min_review_threshold: float,
) -> None:
    filtered = [pair for pair in persist_pairs if pair[2] >= min_review_threshold]
    if filtered:
        insert_similarity_pairs(conn, filtered)
