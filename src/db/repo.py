from __future__ import annotations

import sqlite3
from typing import Any, Dict, List


def insert_pdf(
    conn: sqlite3.Connection,
    pdf_id: str,
    file_path: str,
    checksum: str,
    ingested_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO pdfs(pdf_id, file_path, checksum, ingested_at)
        VALUES(?, ?, ?, ?);
        """,
        (pdf_id, file_path, checksum, ingested_at),
    )
    conn.commit()


def list_pdfs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT pdf_id, file_path, checksum, ingested_at FROM pdfs ORDER BY pdf_id;"
    ).fetchall()
    return [dict(row) for row in rows]


def list_processed_pdfs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT DISTINCT pdfs.pdf_id, pdfs.file_path, pdfs.checksum, pdfs.ingested_at
        FROM pdfs
        JOIN content_blocks ON content_blocks.pdf_id = pdfs.pdf_id
        ORDER BY pdfs.pdf_id;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_pdf_by_checksum(
    conn: sqlite3.Connection, checksum: str
) -> Dict[str, Any] | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT pdf_id, file_path, checksum, ingested_at
        FROM pdfs
        WHERE checksum = ?
        LIMIT 1;
        """,
        (checksum,),
    ).fetchone()
    return dict(row) if row else None


def get_pdf_by_path(conn: sqlite3.Connection, file_path: str) -> Dict[str, Any] | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT pdf_id, file_path, checksum, ingested_at
        FROM pdfs
        WHERE file_path = ?
        LIMIT 1;
        """,
        (file_path,),
    ).fetchone()
    return dict(row) if row else None


def delete_pdf(conn: sqlite3.Connection, pdf_id: str) -> None:
    conn.execute("DELETE FROM pdfs WHERE pdf_id = ?;", (pdf_id,))
    conn.commit()


def clear_derived_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DELETE FROM candidate_embeddings;
        DELETE FROM candidate_similarity;
        DELETE FROM domain_embeddings;
        DELETE FROM block_domain_map;
        DELETE FROM domain_aliases;
        DELETE FROM domain_sources;
        DELETE FROM domains;
        DELETE FROM domain_candidates;
        """
    )
    conn.commit()
