from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from typing import List


@dataclass(frozen=True)
class AppConfig:
    embedding_model: str
    embedding_model_options: List[str]
    merge_threshold_name_only: float
    review_threshold_name_only: float
    merge_threshold_name_plus_summary: float
    review_threshold_name_plus_summary: float
    max_tokens_per_embed: int
    tokenization_fallback_approx_enabled: bool
    preferred_display_language: str


def load_config() -> AppConfig:
    embedding_model_options = ["text-embedding-3-small", "text-embedding-3-large"]
    embedding_model = getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    if embedding_model not in embedding_model_options:
        embedding_model = "text-embedding-3-small"

    return AppConfig(
        embedding_model=embedding_model,
        embedding_model_options=embedding_model_options,
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
    )
