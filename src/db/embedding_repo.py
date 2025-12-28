from __future__ import annotations

import sqlite3
import json
from typing import Any, Dict, List


def insert_candidate_embedding(
    conn: sqlite3.Connection,
    candidate_id: str,
    model_name: str,
    vector: str,
    token_count: int,
    tokenization_mode: str,
) -> None:
    _ensure_json_vector(vector)
    conn.execute(
        """
        INSERT OR REPLACE INTO candidate_embeddings(
            candidate_id, model_name, vector, token_count, tokenization_mode
        )
        VALUES(?, ?, ?, ?, ?);
        """,
        (candidate_id, model_name, vector, token_count, tokenization_mode),
    )
    conn.commit()


def insert_candidate_embedding_vector(
    conn: sqlite3.Connection,
    candidate_id: str,
    model_name: str,
    vector: List[float],
    token_count: int,
    tokenization_mode: str,
) -> None:
    insert_candidate_embedding(
        conn,
        candidate_id=candidate_id,
        model_name=model_name,
        vector=json.dumps(vector),
        token_count=token_count,
        tokenization_mode=tokenization_mode,
    )


def insert_domain_embedding(
    conn: sqlite3.Connection,
    domain_id: str,
    model_name: str,
    vector: str,
    token_count: int,
    tokenization_mode: str,
) -> None:
    _ensure_json_vector(vector)
    conn.execute(
        """
        INSERT OR REPLACE INTO domain_embeddings(
            domain_id, model_name, vector, token_count, tokenization_mode
        )
        VALUES(?, ?, ?, ?, ?);
        """,
        (domain_id, model_name, vector, token_count, tokenization_mode),
    )
    conn.commit()


def insert_domain_embedding_vector(
    conn: sqlite3.Connection,
    domain_id: str,
    model_name: str,
    vector: List[float],
    token_count: int,
    tokenization_mode: str,
) -> None:
    insert_domain_embedding(
        conn,
        domain_id=domain_id,
        model_name=model_name,
        vector=json.dumps(vector),
        token_count=token_count,
        tokenization_mode=tokenization_mode,
    )


def list_candidate_embeddings(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT candidate_id, model_name, vector, token_count, tokenization_mode
        FROM candidate_embeddings
        ORDER BY candidate_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_domain_embeddings(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT domain_id, model_name, vector, token_count, tokenization_mode
        FROM domain_embeddings
        ORDER BY domain_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def parse_vector(vector_text: str) -> List[float]:
    return json.loads(vector_text)


def _ensure_json_vector(vector_text: str) -> None:
    parsed = json.loads(vector_text)
    if not isinstance(parsed, list):
        raise ValueError("vector must be a JSON array")
