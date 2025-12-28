import sqlite3

from src.db.schema import create_schema


def _fetch_names(conn: sqlite3.Connection, obj_type: str) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = ?;", (obj_type,)
    ).fetchall()
    return {row[0] for row in rows}


def test_create_schema_creates_required_tables() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    tables = _fetch_names(conn, "table")
    expected = {
        "pdfs",
        "content_blocks",
        "domain_candidates",
        "candidate_embeddings",
        "candidate_similarity",
        "review_queue",
        "domains",
        "domain_aliases",
        "domain_sources",
        "domain_embeddings",
        "block_domain_map",
        "token_count_cache",
        "trunc_text_cache",
    }

    assert expected.issubset(tables)


def test_create_schema_creates_indexes() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    indexes = _fetch_names(conn, "index")
    expected = {
        "idx_content_blocks_pdf_id",
        "idx_candidates_pdf_id",
        "idx_candidates_norm_name",
        "idx_candidate_similarity_mode",
        "idx_review_queue_status",
        "idx_domain_aliases_domain_id",
        "idx_domain_sources_domain_id",
    }

    assert expected.issubset(indexes)
