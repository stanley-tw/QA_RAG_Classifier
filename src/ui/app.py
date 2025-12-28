from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from os import getenv
from pathlib import Path

import streamlit as st

from src.config import load_config
from src.db.candidate_repo import get_candidate
from src.db.content_repo import delete_content_blocks_for_pdf
from src.db.repo import (
    clear_derived_tables,
    delete_pdf,
    get_pdf_by_checksum,
    get_pdf_by_path,
    insert_pdf,
    list_pdfs,
)
from src.db.review_repo import list_pending_reviews, resolve_review
from src.db.schema import create_schema
from src.db.token_usage_repo import get_latest_run_usage, get_total_usage
from src.pipeline.run import run_pipeline
from src.ui.state import load_domain_list, load_pdf_lists


def render_upload_section() -> None:
    st.subheader("Upload PDFs")
    st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="uploaded_pdfs",
    )


def render_pdf_lists() -> None:
    st.subheader("PDF Lists")
    stored_pdfs = st.session_state.get("stored_pdfs", [])
    processed_pdfs = st.session_state.get("processed_pdfs", [])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Stored PDFs")
        if stored_pdfs:
            st.write(stored_pdfs)
        else:
            st.caption("No stored PDFs yet.")
    with col2:
        st.markdown("Processed PDFs")
        if processed_pdfs:
            st.write(processed_pdfs)
        else:
            st.caption("No processed PDFs yet.")


def render_delete_pdf(config) -> None:
    st.subheader("Delete PDFs (Hard Delete)")
    conn = sqlite3.connect(config.db_path)
    try:
        create_schema(conn)
        pdfs = list_pdfs(conn)
        if not pdfs:
            st.caption("No stored PDFs available.")
            return
        options = {row["file_path"]: row["pdf_id"] for row in pdfs}
        selection = st.selectbox(
            "Select PDF to delete",
            options=list(options.keys()),
            key="delete_pdf_path",
        )
        confirm = st.checkbox(
            "I understand this will delete the stored PDF and reset derived data.",
            key="delete_pdf_confirm",
        )
        if st.button("Delete PDF", type="secondary", disabled=not confirm):
            pdf_id = options.get(selection)
            if not pdf_id:
                st.warning("Invalid PDF selection.")
                return
            existing = get_pdf_by_path(conn, selection)
            if existing:
                pdf_id = existing["pdf_id"]
            delete_content_blocks_for_pdf(conn, pdf_id)
            delete_pdf(conn, pdf_id)
            clear_derived_tables(conn)
            _remove_pdf_file(selection, config.pdf_storage_dir)
            stored_pdfs, processed_pdfs = load_pdf_lists(config.db_path)
            st.session_state["stored_pdfs"] = stored_pdfs
            st.session_state["processed_pdfs"] = processed_pdfs
            st.session_state["domain_list"] = load_domain_list(config.db_path)
            st.success("PDF deleted. Derived data reset.")
    finally:
        conn.close()


def _remove_pdf_file(file_path: str, storage_dir: str) -> None:
    try:
        base = Path(storage_dir).resolve()
        target = Path(file_path).resolve()
        if base in target.parents and target.exists():
            target.unlink()
    except Exception:
        pass

def _safe_filename(name: str) -> str:
    cleaned = []
    for ch in name:
        if ch.isascii() and (ch.isalnum() or ch in {".", "_", "-"}):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("._") or "upload.pdf"


def _persist_uploads(db_path: str, storage_dir: str) -> list[str]:
    uploaded = st.session_state.get("uploaded_pdfs") or []
    if not uploaded:
        return []

    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        stored_paths = []
        for file in uploaded:
            data = file.getvalue()
            checksum = hashlib.sha256(data).hexdigest()
            existing = get_pdf_by_checksum(conn, checksum)
            if existing:
                stored_paths.append(existing["file_path"])
                continue
            safe_name = _safe_filename(file.name)
            target = Path(storage_dir) / f"{checksum}_{safe_name}"
            if not target.exists():
                target.write_bytes(data)
            pdf_id = f"pdf_{checksum}"
            ingested_at = datetime.now(timezone.utc).isoformat()
            insert_pdf(conn, pdf_id, str(target), checksum, ingested_at)
            stored_paths.append(str(target))
        return stored_paths
    finally:
        conn.close()


def render_parameters(config) -> None:
    st.subheader("Parameters")

    st.selectbox(
        "Embedding model",
        options=config.embedding_model_options,
        index=config.embedding_model_options.index(config.embedding_model),
        key="embedding_model",
    )
    st.number_input(
        "Merge threshold (name only)",
        min_value=0.0,
        max_value=1.0,
        value=config.merge_threshold_name_only,
        step=0.01,
        key="merge_threshold_name_only",
    )
    st.number_input(
        "Review threshold (name only)",
        min_value=0.0,
        max_value=1.0,
        value=config.review_threshold_name_only,
        step=0.01,
        key="review_threshold_name_only",
    )
    st.number_input(
        "Merge threshold (name + summary)",
        min_value=0.0,
        max_value=1.0,
        value=config.merge_threshold_name_plus_summary,
        step=0.01,
        key="merge_threshold_name_plus_summary",
    )
    st.number_input(
        "Review threshold (name + summary)",
        min_value=0.0,
        max_value=1.0,
        value=config.review_threshold_name_plus_summary,
        step=0.01,
        key="review_threshold_name_plus_summary",
    )
    st.selectbox(
        "Preferred display language",
        options=["auto", "en", "zh"],
        index=["auto", "en", "zh"].index(config.preferred_display_language),
        key="preferred_display_language",
    )

    run_in_progress = st.session_state.get("run_in_progress", False)
    if st.button("Start RAG", type="primary", disabled=run_in_progress):
        st.session_state["run_in_progress"] = True
        try:
            _persist_uploads(config.db_path, config.pdf_storage_dir)
            stored_pdfs, processed_pdfs = load_pdf_lists(config.db_path)
            if not stored_pdfs:
                st.warning(
                    "No PDFs available. Please upload at least one PDF to run the pipeline."
                )
                return
            azure_endpoint = getenv("AZURE_OPENAI_ENDPOINT")
            azure_api_key = getenv("AZURE_OPENAI_API_KEY")
            azure_ad_token = getenv("AZURE_OPENAI_AD_TOKEN")
            if not azure_endpoint or (not azure_api_key and not azure_ad_token):
                st.error(
                    "Missing Azure OpenAI credentials. Set AZURE_OPENAI_ENDPOINT and "
                    "AZURE_OPENAI_API_KEY (or AZURE_OPENAI_AD_TOKEN) before running."
                )
                return
            st.session_state["stored_pdfs"] = stored_pdfs
            st.session_state["processed_pdfs"] = processed_pdfs
            progress = st.progress(0)
            status = st.empty()
            log_area = st.empty()
            log_lines: list[str] = []

            def report(message: str, pct: float) -> None:
                status.text(message)
                progress.progress(min(max(pct, 0.0), 1.0))
                log_lines.append(message)
                log_area.text_area(
                    "Pipeline log",
                    value="\n".join(log_lines[-200:]),
                    height=200,
                )

            with st.spinner("Running pipeline..."):
                updated_config = replace(
                    config,
                    embedding_model=st.session_state.get(
                        "embedding_model", config.embedding_model
                    ),
                    merge_threshold_name_only=st.session_state.get(
                        "merge_threshold_name_only",
                        config.merge_threshold_name_only,
                    ),
                    review_threshold_name_only=st.session_state.get(
                        "review_threshold_name_only",
                        config.review_threshold_name_only,
                    ),
                    merge_threshold_name_plus_summary=st.session_state.get(
                        "merge_threshold_name_plus_summary",
                        config.merge_threshold_name_plus_summary,
                    ),
                    review_threshold_name_plus_summary=st.session_state.get(
                        "review_threshold_name_plus_summary",
                        config.review_threshold_name_plus_summary,
                    ),
                    preferred_display_language=st.session_state.get(
                        "preferred_display_language",
                        config.preferred_display_language,
                    ),
                )
                try:
                    success = run_pipeline(updated_config, progress_cb=report)
                except Exception as exc:
                    st.error("Pipeline failed. Fix the issue and try again.")
                    st.text_area(
                        "Error details",
                        value=str(exc),
                        height=140,
                    )
                    return
            if success:
                st.success("Pipeline run completed.")
                st.session_state["domain_list"] = load_domain_list(config.db_path)
            else:
                st.warning("No unprocessed PDFs available or no candidates found.")
        finally:
            st.session_state["run_in_progress"] = False


def render_domain_list() -> None:
    st.subheader("Domain List")
    domains = st.session_state.get("domain_list", [])
    if not domains:
        st.caption("No domains available yet.")
        return

    for domain in domains:
        st.markdown(f"- {domain}")


def render_artifact_path(artifact_dir: str) -> None:
    st.subheader("Artifact Bundle")
    st.text(f"Bundle output directory (planned): {artifact_dir}")


def render_review_queue(db_path: str) -> None:
    st.subheader("Review Queue")
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        pending = list_pending_reviews(conn)
        if not pending:
            st.caption("No pending review items.")
            return
        for item in pending:
            candidate_a = get_candidate(conn, item["candidate_a_id"])
            candidate_b = get_candidate(conn, item["candidate_b_id"])
            name_a = candidate_a["candidate_name"] if candidate_a else item["candidate_a_id"]
            name_b = candidate_b["candidate_name"] if candidate_b else item["candidate_b_id"]
            st.markdown(
                f"- **{name_a}** <-> **{name_b}** | similarity={item['similarity']:.3f} | reason={item['reason']}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Accept",
                    key=f"accept_{item['review_id']}",
                ):
                    resolve_review(
                        conn,
                        review_id=item["review_id"],
                        status="accepted",
                        resolved_at=datetime.now(timezone.utc).isoformat(),
                    )
                    st.rerun()
            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_{item['review_id']}",
                ):
                    resolve_review(
                        conn,
                        review_id=item["review_id"],
                        status="rejected",
                        resolved_at=datetime.now(timezone.utc).isoformat(),
                    )
                    st.rerun()
    finally:
        conn.close()


def render_token_usage(db_path: str) -> None:
    st.subheader("Token Usage")
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        latest = get_latest_run_usage(conn)
        totals = get_total_usage(conn)
        if not latest and not totals:
            st.caption("No token usage recorded yet.")
            return
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("Latest run")
            if latest and latest.tokens_by_model:
                for model_name, total in latest.tokens_by_model.items():
                    st.write(f"{model_name}: {total}")
            else:
                st.caption("No run usage available.")
        with col2:
            st.markdown("Cumulative total")
            if totals:
                for model_name, total in totals.items():
                    st.write(f"{model_name}: {total}")
            else:
                st.caption("No totals available.")
    finally:
        conn.close()


def main() -> None:
    st.set_page_config(page_title="Domain Discovery", layout="wide")
    st.title("Canonical Domain Discovery")

    config = load_config()

    render_upload_section()
    stored_pdfs, processed_pdfs = load_pdf_lists(config.db_path)
    st.session_state["stored_pdfs"] = stored_pdfs
    st.session_state["processed_pdfs"] = processed_pdfs
    render_pdf_lists()
    render_parameters(config)
    render_delete_pdf(config)
    render_domain_list()
    render_review_queue(config.db_path)
    render_token_usage(config.db_path)
    render_artifact_path(config.artifact_dir)
    st.subheader("PDF Storage")
    st.text(f"Stored PDF directory: {config.pdf_storage_dir}")


if __name__ == "__main__":
    main()
