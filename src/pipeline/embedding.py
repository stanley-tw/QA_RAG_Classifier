from __future__ import annotations

import json
from dataclasses import dataclass
from os import getenv
from typing import List, Sequence

from openai import AzureOpenAI

from src.db.token_cache_repo import (
    get_token_count_cache_for_text,
    get_trunc_text_cache_for_text,
    set_token_count_cache_for_text,
    set_trunc_text_cache_for_text,
)
from src.pipeline.tokenization import count_tokens_with_mode, truncate_text_with_mode


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: List[List[float]]
    token_counts: List[int]
    tokenization_mode: str
    truncated_texts: List[str]
    total_tokens: int


class AzureOpenAIEmbedder:
    def __init__(
        self,
        model_name: str,
        max_tokens: int,
        approx_enabled: bool,
        client: AzureOpenAI | None = None,
    ) -> None:
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.approx_enabled = approx_enabled
        self.client = client or AzureOpenAI(
            api_key=getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        )

    def embed_texts(
        self, conn, texts: Sequence[str], batch_size: int = 16
    ) -> EmbeddingResult:
        truncated_texts, token_counts, mode = _prepare_texts(
            conn,
            texts,
            self.model_name,
            self.max_tokens,
            self.approx_enabled,
        )
        vectors: List[List[float]] = []
        total_tokens = 0
        for i in range(0, len(truncated_texts), batch_size):
            batch = truncated_texts[i : i + batch_size]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch,
            )
            vectors.extend([item.embedding for item in response.data])
            usage = getattr(response, "usage", None)
            if usage and getattr(usage, "total_tokens", None) is not None:
                total_tokens += int(usage.total_tokens)
            else:
                total_tokens += sum(token_counts[i : i + batch_size])
        return EmbeddingResult(
            vectors=vectors,
            token_counts=token_counts,
            tokenization_mode=mode,
            truncated_texts=truncated_texts,
            total_tokens=total_tokens,
        )


def _prepare_texts(conn, texts, model_name, max_tokens, approx_enabled):
    truncated_texts: List[str] = []
    token_counts: List[int] = []
    tokenization_mode = "exact"
    for text in texts:
        trunc_cache = get_trunc_text_cache_for_text(conn, text, model_name, max_tokens)
        if trunc_cache:
            truncated = trunc_cache["truncated_text"]
            if trunc_cache["tokenization_mode"] == "approx":
                tokenization_mode = "approx"
        else:
            truncated, tokenization_mode = truncate_text_with_mode(
                text, model_name=model_name, max_tokens=max_tokens, approx_enabled=approx_enabled
            )
            set_trunc_text_cache_for_text(
                conn,
                text=text,
                model_name=model_name,
                max_tokens=max_tokens,
                truncated_text=truncated,
                tokenization_mode=tokenization_mode,
            )
        count_cache = get_token_count_cache_for_text(conn, truncated, model_name)
        if count_cache:
            token_count = count_cache["token_count"]
        else:
            token_count, mode = count_tokens_with_mode(
                truncated, model_name=model_name, approx_enabled=approx_enabled
            )
            if mode == "approx":
                tokenization_mode = "approx"
            set_token_count_cache_for_text(
                conn,
                text=truncated,
                model_name=model_name,
                token_count=token_count,
                tokenization_mode=tokenization_mode,
            )
        truncated_texts.append(truncated)
        token_counts.append(token_count)
    return truncated_texts, token_counts, tokenization_mode


def serialize_vector(vector: Sequence[float]) -> str:
    return json.dumps(list(vector))
