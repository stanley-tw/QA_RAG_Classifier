from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from src.db.domain_repo import list_domains
from src.db.repo import list_pdfs, list_processed_pdfs
from src.db.schema import create_schema


def load_domain_list(db_path: str) -> List[str]:
    path = Path(db_path)
    if not path.exists():
        return []

    conn = sqlite3.connect(path)
    try:
        create_schema(conn)
        domains = list_domains(conn)
        return [f"{d['domain_id']}: {d['display_name']}" for d in domains]
    finally:
        conn.close()


def load_pdf_lists(db_path: str) -> tuple[List[str], List[str]]:
    path = Path(db_path)
    if not path.exists():
        return ([], [])

    conn = sqlite3.connect(path)
    try:
        create_schema(conn)
        stored = list_pdfs(conn)
        processed = list_processed_pdfs(conn)
        stored_list = [row["file_path"] for row in stored]
        processed_list = [row["file_path"] for row in processed]
        return (stored_list, processed_list)
    finally:
        conn.close()
