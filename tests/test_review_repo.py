import sqlite3
from datetime import datetime, timezone

from src.db.review_repo import (
    has_review_pair,
    insert_review_item,
    list_pending_reviews,
    list_rejected_pairs,
    resolve_review,
)
from src.db.schema import create_schema


def test_review_queue_insert_and_list_pending() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    insert_review_item(
        conn,
        review_id="r1",
        candidate_a_id="c1",
        candidate_b_id="c2",
        similarity=0.87,
        reason="review_band",
        status="pending",
        created_at=now,
    )

    pending = list_pending_reviews(conn)
    assert len(pending) == 1
    assert pending[0]["review_id"] == "r1"


def test_review_queue_resolve() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    insert_review_item(
        conn,
        review_id="r2",
        candidate_a_id="c1",
        candidate_b_id="c2",
        similarity=0.87,
        reason="review_band",
        status="pending",
        created_at=now,
    )

    resolved_at = datetime.now(timezone.utc).isoformat()
    resolve_review(conn, review_id="r2", status="approved", resolved_at=resolved_at)

    pending = list_pending_reviews(conn)
    assert pending == []


def test_review_queue_pair_helpers() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    now = datetime.now(timezone.utc).isoformat()
    insert_review_item(
        conn,
        review_id="r3",
        candidate_a_id="c1",
        candidate_b_id="c2",
        similarity=0.9,
        reason="review_band",
        status="rejected",
        created_at=now,
    )
    assert has_review_pair(conn, "c1", "c2") is True
    assert has_review_pair(conn, "c2", "c1") is True
    rejected = list_rejected_pairs(conn)
    assert ("c1", "c2") in rejected
