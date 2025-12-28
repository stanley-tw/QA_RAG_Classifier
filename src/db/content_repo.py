from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List


def insert_content_blocks(
    conn: sqlite3.Connection, blocks: Iterable[Dict[str, Any]]
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO content_blocks(
            block_id,
            pdf_id,
            section_path,
            heading_level,
            block_type,
            text,
            page_index,
            position_index
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?);
        """,
        [
            (
                block["block_id"],
                block["pdf_id"],
                block.get("section_path"),
                block.get("heading_level"),
                block.get("block_type"),
                block.get("text"),
                block.get("page_index"),
                block.get("position_index"),
            )
            for block in blocks
        ],
    )
    conn.commit()


def list_content_blocks(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT block_id, pdf_id, section_path, heading_level, block_type,
               text, page_index, position_index
        FROM content_blocks
        ORDER BY pdf_id, position_index;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_content_blocks_by_pdf(
    conn: sqlite3.Connection, pdf_id: str
) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT block_id, pdf_id, section_path, heading_level, block_type,
               text, page_index, position_index
        FROM content_blocks
        WHERE pdf_id = ?
        ORDER BY position_index;
        """,
        (pdf_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def has_content_blocks_for_pdf(conn: sqlite3.Connection, pdf_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM content_blocks WHERE pdf_id = ? LIMIT 1;", (pdf_id,)
    ).fetchone()
    return row is not None


def delete_content_blocks_for_pdf(conn: sqlite3.Connection, pdf_id: str) -> None:
    conn.execute("DELETE FROM content_blocks WHERE pdf_id = ?;", (pdf_id,))
    conn.commit()


def clear_content_blocks(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM content_blocks;")
    conn.commit()
