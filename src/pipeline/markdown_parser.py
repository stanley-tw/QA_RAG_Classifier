from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class MarkdownBlock:
    block_type: str
    text: str
    heading_level: int
    section_path: str


def parse_markdown(markdown: str) -> List[MarkdownBlock]:
    lines = markdown.splitlines()
    blocks: List[MarkdownBlock] = []
    heading_stack: List[str] = []
    heading_levels: List[int] = []
    paragraph_lines: List[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines).strip()
            if text:
                blocks.append(
                    MarkdownBlock(
                        block_type="paragraph",
                        text=text,
                        heading_level=heading_levels[-1] if heading_levels else 0,
                        section_path=" > ".join(heading_stack),
                    )
                )
            paragraph_lines.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("#"):
            flush_paragraph()
            level = len(line) - len(line.lstrip("#"))
            heading_text = line.lstrip("#").strip()
            if not heading_text:
                continue
            while heading_levels and heading_levels[-1] >= level:
                heading_levels.pop()
                heading_stack.pop()
            heading_levels.append(level)
            heading_stack.append(heading_text)
            blocks.append(
                MarkdownBlock(
                    block_type="heading",
                    text=heading_text,
                    heading_level=level,
                    section_path=" > ".join(heading_stack),
                )
            )
            continue
        paragraph_lines.append(line)

    flush_paragraph()
    return blocks
