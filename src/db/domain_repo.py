from __future__ import annotations

import sqlite3
from typing import Any, Dict, List


def insert_domain(
    conn: sqlite3.Connection, domain_id: str, display_name: str, created_at: str
) -> None:
    conn.execute(
        """
        INSERT INTO domains(domain_id, display_name, created_at)
        VALUES(?, ?, ?);
        """,
        (domain_id, display_name, created_at),
    )
    conn.commit()


def list_domains(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT domain_id, display_name, created_at FROM domains ORDER BY domain_id;"
    ).fetchall()
    return [dict(row) for row in rows]


def insert_domain_alias(
    conn: sqlite3.Connection,
    domain_id: str,
    alias: str,
    source_pdf_id: str,
    heading_level: int,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO domain_aliases(domain_id, alias, source_pdf_id, heading_level)
        VALUES(?, ?, ?, ?);
        """,
        (domain_id, alias, source_pdf_id, heading_level),
    )
    conn.commit()


def insert_domain_source(conn: sqlite3.Connection, domain_id: str, pdf_id: str) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO domain_sources(domain_id, pdf_id)
        VALUES(?, ?);
        """,
        (domain_id, pdf_id),
    )
    conn.commit()


def insert_block_domain_map(
    conn: sqlite3.Connection, block_id: str, domain_id: str
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO block_domain_map(block_id, domain_id)
        VALUES(?, ?);
        """,
        (block_id, domain_id),
    )
    conn.commit()


def list_domain_aliases(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT domain_id, alias, source_pdf_id, heading_level
        FROM domain_aliases
        ORDER BY domain_id, alias;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_domain_sources(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT domain_id, pdf_id
        FROM domain_sources
        ORDER BY domain_id, pdf_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_block_domain_map(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT block_id, domain_id
        FROM block_domain_map
        ORDER BY block_id, domain_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]
