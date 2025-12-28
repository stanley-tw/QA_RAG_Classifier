import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from src.db.domain_repo import insert_domain
from src.db.schema import create_schema
from src.ui.state import load_domain_list


def test_load_domain_list_reads_from_db(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    insert_domain(
        conn,
        domain_id="domain_001",
        display_name="Payments",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    conn.close()

    result = load_domain_list(str(db_path))
    assert result == ["domain_001: Payments"]
