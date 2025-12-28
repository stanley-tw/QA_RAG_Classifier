from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from raganything.parser import DoclingParser, MineruParser


@dataclass(frozen=True)
class ParsedDocument:
    content_list: List[Dict[str, Any]]
    markdown: str
    parser_name: str
    parse_method: str


def parse_document(
    file_path: str,
    output_dir: str,
    parser_name: str,
    parse_method: str,
) -> ParsedDocument:
    parser = _get_parser(parser_name)
    content_list = parser.parse_document(
        file_path=file_path, method=parse_method, output_dir=output_dir
    )
    markdown = ""
    if hasattr(parser, "_read_output_files"):
        file_stem = Path(file_path).stem
        base_output_dir = Path(output_dir)
        content_list, markdown = parser._read_output_files(
            base_output_dir, file_stem, parse_method
        )
    return ParsedDocument(
        content_list=content_list,
        markdown=markdown,
        parser_name=parser_name,
        parse_method=parse_method,
    )


def _get_parser(parser_name: str):
    name = parser_name.lower()
    if name == "docling":
        return DoclingParser()
    if name == "mineru":
        return MineruParser()
    raise ValueError(f"Unsupported parser: {parser_name}")
