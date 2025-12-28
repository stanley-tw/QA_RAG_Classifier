from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List, Tuple


def insert_similarity_pairs(
    conn: sqlite3.Connection, pairs: Iterable[Tuple[str, str, float, str]]
) -> None:
    conn.executemany(
        """
        INSERT INTO candidate_similarity(candidate_a_id, candidate_b_id, similarity, mode)
        VALUES(?, ?, ?, ?);
        """,
        list(pairs),
    )
    conn.commit()


def list_similarity_pairs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT candidate_a_id, candidate_b_id, similarity, mode
        FROM candidate_similarity
        ORDER BY candidate_a_id, candidate_b_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]
