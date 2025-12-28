import sqlite3
from datetime import datetime, timezone

from src.db.repo import get_pdf_by_checksum, insert_pdf, list_pdfs
from src.db.schema import create_schema


def test_insert_and_list_pdfs() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    insert_pdf(conn, pdf_id="pdf1", file_path="a.pdf", checksum="abc", ingested_at=now)

    rows = list_pdfs(conn)
    assert len(rows) == 1
    assert rows[0]["pdf_id"] == "pdf1"
    assert rows[0]["file_path"] == "a.pdf"


def test_get_pdf_by_checksum() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    now = datetime.now(timezone.utc).isoformat()
    insert_pdf(conn, pdf_id="pdf1", file_path="a.pdf", checksum="abc", ingested_at=now)
    found = get_pdf_by_checksum(conn, "abc")
    missing = get_pdf_by_checksum(conn, "missing")
    assert found is not None
    assert found["pdf_id"] == "pdf1"
    assert missing is None
