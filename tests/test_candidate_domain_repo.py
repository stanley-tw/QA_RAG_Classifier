import sqlite3
from datetime import datetime, timezone

from src.db.candidate_repo import get_candidate, insert_candidate, list_candidates
from src.db.domain_repo import insert_domain, list_domains
from src.db.schema import create_schema


def test_candidate_repo_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_candidate(
        conn,
        candidate_id="c1",
        candidate_name="Payments",
        normalized_name="payments",
        source_pdf_id="p1",
        source_block_id="b1",
        heading_level=1,
        representative_text="Payments section",
    )
    rows = list_candidates(conn)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "c1"


def test_candidate_get_by_id() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_candidate(
        conn,
        candidate_id="c1",
        candidate_name="Payments",
        normalized_name="payments",
        source_pdf_id="p1",
        source_block_id="b1",
        heading_level=1,
        representative_text="Payments section",
    )
    found = get_candidate(conn, "c1")
    missing = get_candidate(conn, "c2")
    assert found is not None
    assert found["candidate_name"] == "Payments"
    assert missing is None


def test_domain_repo_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    insert_domain(conn, domain_id="domain_001", display_name="Payments", created_at=now)
    rows = list_domains(conn)
    assert len(rows) == 1
    assert rows[0]["domain_id"] == "domain_001"
