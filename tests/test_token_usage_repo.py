import sqlite3

from src.db.schema import create_schema
from src.db.token_usage_repo import (
    get_latest_run_usage,
    get_total_usage,
    insert_token_usage,
)


def test_token_usage_repo_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_token_usage(
        conn,
        run_id="run_a",
        model_name="text-embedding-3-small",
        total_tokens=120,
        created_at="2025-01-01T00:00:00Z",
    )
    insert_token_usage(
        conn,
        run_id="run_b",
        model_name="text-embedding-3-small",
        total_tokens=80,
        created_at="2025-01-02T00:00:00Z",
    )
    insert_token_usage(
        conn,
        run_id="run_b",
        model_name="text-embedding-3-large",
        total_tokens=200,
        created_at="2025-01-02T00:00:00Z",
    )

    latest = get_latest_run_usage(conn)
    assert latest is not None
    assert latest.run_id == "run_b"
    assert latest.tokens_by_model == {
        "text-embedding-3-large": 200,
        "text-embedding-3-small": 80,
    }

    totals = get_total_usage(conn)
    assert totals == {
        "text-embedding-3-large": 200,
        "text-embedding-3-small": 200,
    }
