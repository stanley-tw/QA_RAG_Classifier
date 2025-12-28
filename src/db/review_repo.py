from __future__ import annotations

import sqlite3
from typing import Any, Dict, List


def insert_review_item(
    conn: sqlite3.Connection,
    review_id: str,
    candidate_a_id: str,
    candidate_b_id: str,
    similarity: float,
    reason: str,
    status: str,
    created_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO review_queue(
            review_id,
            candidate_a_id,
            candidate_b_id,
            similarity,
            reason,
            status,
            created_at
        )
        VALUES(?, ?, ?, ?, ?, ?, ?);
        """,
        (review_id, candidate_a_id, candidate_b_id, similarity, reason, status, created_at),
    )
    conn.commit()


def list_pending_reviews(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT review_id, candidate_a_id, candidate_b_id, similarity, reason, status
        FROM review_queue
        WHERE status = 'pending'
        ORDER BY created_at;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_rejected_pairs(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT candidate_a_id, candidate_b_id
        FROM review_queue
        WHERE status = 'rejected';
        """
    ).fetchall()
    return {(row["candidate_a_id"], row["candidate_b_id"]) for row in rows}


def has_review_pair(conn: sqlite3.Connection, a: str, b: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM review_queue
        WHERE (candidate_a_id = ? AND candidate_b_id = ?)
           OR (candidate_a_id = ? AND candidate_b_id = ?)
        LIMIT 1;
        """,
        (a, b, b, a),
    ).fetchone()
    return row is not None


def resolve_review(
    conn: sqlite3.Connection, review_id: str, status: str, resolved_at: str
) -> None:
    conn.execute(
        """
        UPDATE review_queue
        SET status = ?, resolved_at = ?
        WHERE review_id = ?;
        """,
        (status, resolved_at, review_id),
    )
    conn.commit()
