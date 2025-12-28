from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List


@dataclass(frozen=True)
class ContentBlock:
    block_id: str
    pdf_id: str
    section_path: str
    heading_level: int
    block_type: str
    text: str
    page_index: int
    position_index: int


@dataclass(frozen=True)
class DomainCandidate:
    candidate_id: str
    candidate_name: str
    normalized_name: str
    source_pdf_id: str
    source_block_id: str
    heading_level: int
    representative_text: str


_MARKERS = ("domain", "subsystem", "module")


def normalize_name(text: str) -> str:
    cleaned = text.strip().lower()
    for marker in _MARKERS:
        cleaned = re.sub(rf"^{re.escape(marker)}\s*[:\-]\s*", "", cleaned)
        cleaned = re.sub(rf"^{re.escape(marker)}\s+", "", cleaned)
    cleaned = cleaned.strip("-: ")
    return " ".join(cleaned.split())


def _extract_marker_name(text: str) -> str | None:
    lowered = text.strip().lower()
    for marker in _MARKERS:
        prefix = f"{marker}:"
        if lowered.startswith(prefix):
            return text.split(":", 1)[1].strip()
    return None


def extract_candidates(blocks: Iterable[ContentBlock]) -> List[DomainCandidate]:
    candidates: List[DomainCandidate] = []
    for block in blocks:
        if block.block_type == "heading":
            name = block.text.strip()
            candidates.append(
                DomainCandidate(
                    candidate_id=block.block_id,
                    candidate_name=name,
                    normalized_name=normalize_name(name),
                    source_pdf_id=block.pdf_id,
                    source_block_id=block.block_id,
                    heading_level=block.heading_level,
                    representative_text=name,
                )
            )
            continue

        if block.block_type == "paragraph":
            extracted = _extract_marker_name(block.text)
            if extracted:
                candidates.append(
                    DomainCandidate(
                        candidate_id=block.block_id,
                        candidate_name=extracted,
                        normalized_name=normalize_name(extracted),
                        source_pdf_id=block.pdf_id,
                        source_block_id=block.block_id,
                        heading_level=block.heading_level,
                        representative_text=block.text.strip(),
                    )
                )

    return candidates
