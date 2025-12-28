import sqlite3
from datetime import datetime, timezone

from src.db.content_repo import delete_content_blocks_for_pdf, insert_content_blocks
from src.db.repo import clear_derived_tables, delete_pdf, insert_pdf, list_pdfs
from src.db.schema import create_schema


def test_delete_pdf_and_clear_blocks() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    now = datetime.now(timezone.utc).isoformat()
    insert_pdf(conn, pdf_id="pdf1", file_path="a.pdf", checksum="abc", ingested_at=now)
    insert_content_blocks(
        conn,
        [
            {
                "block_id": "b1",
                "pdf_id": "pdf1",
                "section_path": "",
                "heading_level": 0,
                "block_type": "paragraph",
                "text": "Body",
                "page_index": 0,
                "position_index": 0,
            }
        ],
    )
    delete_content_blocks_for_pdf(conn, "pdf1")
    delete_pdf(conn, "pdf1")
    clear_derived_tables(conn)
    rows = list_pdfs(conn)
    assert rows == []
