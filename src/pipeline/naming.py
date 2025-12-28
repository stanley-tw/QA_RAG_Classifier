from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class AliasInfo:
    alias: str
    source_pdf_id: str
    heading_level: int


def select_display_name(
    aliases: Iterable[AliasInfo], preferred_language: str
) -> str:
    alias_list = list(aliases)
    if not alias_list:
        return "unknown"

    freq_by_alias: dict[str, set[str]] = {}
    best_heading_by_alias: dict[str, int] = {}
    for item in alias_list:
        freq_by_alias.setdefault(item.alias, set()).add(item.source_pdf_id)
        best_heading_by_alias[item.alias] = min(
            item.heading_level, best_heading_by_alias.get(item.alias, item.heading_level)
        )

    scored = []
    for alias, pdfs in freq_by_alias.items():
        freq = len(pdfs)
        heading_level = best_heading_by_alias[alias]
        length = len(alias.strip())
        lang_penalty = _language_penalty(alias, preferred_language)
        scored.append((-freq, heading_level, lang_penalty, length, alias))

    scored.sort()
    return scored[0][-1]


def should_use_llm_fallback(aliases: Sequence[str]) -> bool:
    if not aliases:
        return True
    normalized = [_normalize_alias(a) for a in aliases]
    if all(a in _LOW_SIGNAL_ALIASES for a in normalized):
        return True
    return _max_jaccard_similarity(normalized) < 0.3


def build_llm_naming_request(
    aliases: Sequence[str], snippets: Sequence[str], language: str
) -> dict:
    return {
        "aliases": list(aliases),
        "snippets": list(snippets),
        "language": language,
        "output_schema": {"display_name": "string", "summary": "string", "keywords": []},
        "constraints": [
            "Do not invent concepts not supported by aliases/snippets.",
            "Use only terms grounded in provided inputs.",
        ],
    }


def _language_penalty(text: str, preferred_language: str) -> int:
    if preferred_language == "auto":
        return 0 if _is_english(text) else 1
    is_en = _is_english(text)
    if preferred_language == "en":
        return 0 if is_en else 1
    if preferred_language == "zh":
        return 0 if not is_en else 1
    return 0


def _is_english(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text) and any(ch.isalpha() for ch in text)


_LOW_SIGNAL_ALIASES = {
    "overview",
    "introduction",
    "general",
    "summary",
    "background",
}


def _normalize_alias(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _max_jaccard_similarity(items: Sequence[str]) -> float:
    max_sim = 0.0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            set_a = set(items[i].split())
            set_b = set(items[j].split())
            if not set_a or not set_b:
                continue
            sim = len(set_a & set_b) / len(set_a | set_b)
            max_sim = max(max_sim, sim)
    return max_sim
