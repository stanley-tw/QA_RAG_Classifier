from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TokenUsageSummary:
    run_id: str
    tokens_by_model: Dict[str, int]


def insert_token_usage(
    conn: sqlite3.Connection,
    run_id: str,
    model_name: str,
    total_tokens: int,
    created_at: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO token_usage(
            run_id, model_name, total_tokens, created_at
        )
        VALUES(?, ?, ?, ?);
        """,
        (run_id, model_name, total_tokens, created_at),
    )


def get_latest_run_usage(conn: sqlite3.Connection) -> TokenUsageSummary | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT run_id
        FROM token_usage
        ORDER BY created_at DESC, run_id DESC
        LIMIT 1;
        """
    ).fetchone()
    if not row:
        return None
    run_id = row["run_id"]
    rows = conn.execute(
        """
        SELECT model_name, total_tokens
        FROM token_usage
        WHERE run_id = ?
        ORDER BY model_name;
        """,
        (run_id,),
    ).fetchall()
    tokens_by_model = {item["model_name"]: item["total_tokens"] for item in rows}
    return TokenUsageSummary(run_id=run_id, tokens_by_model=tokens_by_model)


def get_total_usage(conn: sqlite3.Connection) -> Dict[str, int]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT model_name, SUM(total_tokens) AS total_tokens
        FROM token_usage
        GROUP BY model_name
        ORDER BY model_name;
        """
    ).fetchall()
    return {row["model_name"]: row["total_tokens"] for row in rows}
