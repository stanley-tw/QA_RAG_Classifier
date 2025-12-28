from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from typing import List


@dataclass(frozen=True)
class AppConfig:
    embedding_model: str
    embedding_model_options: List[str]
    embedding_dimensions: dict[str, int]
    merge_threshold_name_only: float
    review_threshold_name_only: float
    merge_threshold_name_plus_summary: float
    review_threshold_name_plus_summary: float
    max_tokens_per_embed: int
    tokenization_fallback_approx_enabled: bool
    preferred_display_language: str
    db_path: str
    pdf_storage_dir: str
    rag_parser: str
    rag_parse_method: str
    rag_output_dir: str
    skip_processed_pdfs: bool
    artifact_dir: str


def load_config() -> AppConfig:
    embedding_model_options = ["text-embedding-3-small", "text-embedding-3-large"]
    embedding_dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }
    return AppConfig(
        embedding_model=getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_model_options=embedding_model_options,
        embedding_dimensions=embedding_dimensions,
        merge_threshold_name_only=float(getenv("MERGE_THRESHOLD_NAME_ONLY", "0.90")),
        review_threshold_name_only=float(getenv("REVIEW_THRESHOLD_NAME_ONLY", "0.85")),
        merge_threshold_name_plus_summary=float(
            getenv("MERGE_THRESHOLD_NAME_PLUS_SUMMARY", "0.86")
        ),
        review_threshold_name_plus_summary=float(
            getenv("REVIEW_THRESHOLD_NAME_PLUS_SUMMARY", "0.82")
        ),
        max_tokens_per_embed=int(getenv("MAX_TOKENS_PER_EMBED", "8192")),
        tokenization_fallback_approx_enabled=getenv(
            "TOKENIZATION_FALLBACK_APPROX_ENABLED", "false"
        ).lower()
        == "true",
        preferred_display_language=getenv("PREFERRED_DISPLAY_LANGUAGE", "auto"),
        db_path=getenv("DB_PATH", "./data/app.db"),
        pdf_storage_dir=getenv("PDF_STORAGE_DIR", "./data/pdfs"),
        rag_parser=getenv("RAG_PARSER", "mineru"),
        rag_parse_method=getenv("RAG_PARSE_METHOD", "auto"),
        rag_output_dir=getenv("RAG_OUTPUT_DIR", "./data/rag_output"),
        skip_processed_pdfs=getenv("SKIP_PROCESSED_PDFS", "true").lower() == "true",
        artifact_dir=getenv("ARTIFACT_DIR", "./artifacts"),
    )
