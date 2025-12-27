from __future__ import annotations

import streamlit as st

from src.config import load_config


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

    if st.button("Start RAG", type="primary"):
        st.info("Pipeline execution is not wired yet.")


def render_domain_list() -> None:
    st.subheader("Domain List")
    domains = st.session_state.get("domain_list", [])
    if not domains:
        st.caption("No domains available yet.")
        return

    for domain in domains:
        st.markdown(f"- {domain}")


def main() -> None:
    st.set_page_config(page_title="Domain Discovery", layout="wide")
    st.title("Canonical Domain Discovery")

    config = load_config()

    render_upload_section()
    render_pdf_lists()
    render_parameters(config)
    render_domain_list()


if __name__ == "__main__":
    main()
