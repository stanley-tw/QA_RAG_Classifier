from __future__ import annotations

import sqlite3
from typing import Any, Dict, List


def insert_candidate(
    conn: sqlite3.Connection,
    candidate_id: str,
    candidate_name: str,
    normalized_name: str,
    source_pdf_id: str,
    source_block_id: str,
    heading_level: int,
    representative_text: str,
) -> None:
    conn.execute(
        """
        INSERT INTO domain_candidates(
            candidate_id,
            candidate_name,
            normalized_name,
            source_pdf_id,
            source_block_id,
            heading_level,
            representative_text
        )
        VALUES(?, ?, ?, ?, ?, ?, ?);
        """,
        (
            candidate_id,
            candidate_name,
            normalized_name,
            source_pdf_id,
            source_block_id,
            heading_level,
            representative_text,
        ),
    )
    conn.commit()


def list_candidates(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT candidate_id, candidate_name, normalized_name, source_pdf_id,
               source_block_id, heading_level, representative_text
        FROM domain_candidates
        ORDER BY candidate_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_candidate(conn: sqlite3.Connection, candidate_id: str) -> Dict[str, Any] | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT candidate_id, candidate_name, normalized_name, source_pdf_id,
               source_block_id, heading_level, representative_text
        FROM domain_candidates
        WHERE candidate_id = ?
        LIMIT 1;
        """,
        (candidate_id,),
    ).fetchone()
    return dict(row) if row else None
