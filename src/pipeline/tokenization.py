from __future__ import annotations

import math
from typing import Protocol


class Encoding(Protocol):
    def encode(self, text: str) -> list[int]: ...
    def decode(self, tokens: list[int]) -> str: ...


def _get_tiktoken_encoding(model_name: str) -> Encoding:
    import tiktoken

    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def _approx_token_count(text: str) -> int:
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    non_ascii_chars = len(text) - ascii_chars
    approx = ascii_chars / 4.0 + non_ascii_chars * 1.0
    return int(math.ceil(approx))


def count_tokens(text: str, model_name: str, approx_enabled: bool) -> int:
    try:
        encoding = _get_tiktoken_encoding(model_name)
    except Exception:
        if not approx_enabled:
            raise
        return _approx_token_count(text)

    return len(encoding.encode(text))


def count_tokens_with_mode(
    text: str, model_name: str, approx_enabled: bool
) -> tuple[int, str]:
    try:
        encoding = _get_tiktoken_encoding(model_name)
    except Exception:
        if not approx_enabled:
            raise
        return _approx_token_count(text), "approx"

    return len(encoding.encode(text)), "exact"


def truncate_text(text: str, model_name: str, max_tokens: int, approx_enabled: bool) -> str:
    try:
        encoding = _get_tiktoken_encoding(model_name)
    except Exception:
        if not approx_enabled:
            raise
        return _approx_truncate(text, max_tokens)

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


def truncate_text_with_mode(
    text: str, model_name: str, max_tokens: int, approx_enabled: bool
) -> tuple[str, str]:
    try:
        encoding = _get_tiktoken_encoding(model_name)
    except Exception:
        if not approx_enabled:
            raise
        return _approx_truncate(text, max_tokens), "approx"

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text, "exact"
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens), "exact"


def _approx_truncate(text: str, max_tokens: int) -> str:
    safe_limit = max_tokens * 0.7
    total = 0.0
    end_index = 0
    for idx, ch in enumerate(text):
        total += 0.25 if ord(ch) < 128 else 1.0
        if total > safe_limit:
            break
        end_index = idx + 1
    return text[:end_index]
