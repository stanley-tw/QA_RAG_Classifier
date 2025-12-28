import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from src.db.repo import insert_pdf
from src.db.schema import create_schema
from src.ui.state import load_pdf_lists


def test_load_pdf_lists_returns_stored_and_processed(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    insert_pdf(
        conn,
        pdf_id="p1",
        file_path="a.pdf",
        checksum="abc",
        ingested_at=datetime.now(timezone.utc).isoformat(),
    )
    conn.execute(
        """
        INSERT INTO content_blocks(
            block_id, pdf_id, section_path, heading_level, block_type,
            text, page_index, position_index
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?);
        """,
        ("b1", "p1", "1", 1, "heading", "Title", 1, 1),
    )
    conn.commit()
    conn.close()

    stored, processed = load_pdf_lists(str(db_path))
    assert stored == ["a.pdf"]
    assert processed == ["a.pdf"]
