import sqlite3

from src.db.content_repo import (
    clear_content_blocks,
    has_content_blocks_for_pdf,
    insert_content_blocks,
    list_content_blocks_by_pdf,
)
from src.db.schema import create_schema


def test_content_block_round_trip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    blocks = [
        {
            "block_id": "b1",
            "pdf_id": "pdf1",
            "section_path": "Intro",
            "heading_level": 1,
            "block_type": "heading",
            "text": "Intro",
            "page_index": 0,
            "position_index": 0,
        },
        {
            "block_id": "b2",
            "pdf_id": "pdf1",
            "section_path": "Intro",
            "heading_level": 1,
            "block_type": "paragraph",
            "text": "Body",
            "page_index": 0,
            "position_index": 1,
        },
    ]
    insert_content_blocks(conn, blocks)
    assert has_content_blocks_for_pdf(conn, "pdf1") is True
    stored = list_content_blocks_by_pdf(conn, "pdf1")
    assert len(stored) == 2
    clear_content_blocks(conn)
    assert has_content_blocks_for_pdf(conn, "pdf1") is False
