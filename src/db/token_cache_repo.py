from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional

from src.pipeline.hash_utils import text_hash


def set_token_count_cache(
    conn: sqlite3.Connection,
    text_hash: str,
    model_name: str,
    token_count: int,
    tokenization_mode: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO token_count_cache(
            text_hash, model_name, token_count, tokenization_mode
        )
        VALUES(?, ?, ?, ?);
        """,
        (text_hash, model_name, token_count, tokenization_mode),
    )
    conn.commit()


def get_token_count_cache(
    conn: sqlite3.Connection, text_hash: str, model_name: str
) -> Optional[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT text_hash, model_name, token_count, tokenization_mode
        FROM token_count_cache
        WHERE text_hash = ? AND model_name = ?;
        """,
        (text_hash, model_name),
    ).fetchone()
    return dict(row) if row else None


def set_token_count_cache_for_text(
    conn: sqlite3.Connection,
    text: str,
    model_name: str,
    token_count: int,
    tokenization_mode: str,
) -> None:
    set_token_count_cache(
        conn,
        text_hash=text_hash(text),
        model_name=model_name,
        token_count=token_count,
        tokenization_mode=tokenization_mode,
    )


def get_token_count_cache_for_text(
    conn: sqlite3.Connection, text: str, model_name: str
) -> Optional[Dict[str, Any]]:
    return get_token_count_cache(conn, text_hash=text_hash(text), model_name=model_name)


def set_trunc_text_cache(
    conn: sqlite3.Connection,
    text_hash: str,
    model_name: str,
    max_tokens: int,
    truncated_text: str,
    tokenization_mode: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO trunc_text_cache(
            text_hash, model_name, max_tokens, truncated_text, tokenization_mode
        )
        VALUES(?, ?, ?, ?, ?);
        """,
        (text_hash, model_name, max_tokens, truncated_text, tokenization_mode),
    )
    conn.commit()


def get_trunc_text_cache(
    conn: sqlite3.Connection, text_hash: str, model_name: str, max_tokens: int
) -> Optional[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT text_hash, model_name, max_tokens, truncated_text, tokenization_mode
        FROM trunc_text_cache
        WHERE text_hash = ? AND model_name = ? AND max_tokens = ?;
        """,
        (text_hash, model_name, max_tokens),
    ).fetchone()
    return dict(row) if row else None


def set_trunc_text_cache_for_text(
    conn: sqlite3.Connection,
    text: str,
    model_name: str,
    max_tokens: int,
    truncated_text: str,
    tokenization_mode: str,
) -> None:
    set_trunc_text_cache(
        conn,
        text_hash=text_hash(text),
        model_name=model_name,
        max_tokens=max_tokens,
        truncated_text=truncated_text,
        tokenization_mode=tokenization_mode,
    )


def get_trunc_text_cache_for_text(
    conn: sqlite3.Connection, text: str, model_name: str, max_tokens: int
) -> Optional[Dict[str, Any]]:
    return get_trunc_text_cache(
        conn, text_hash=text_hash(text), model_name=model_name, max_tokens=max_tokens
    )
