import sqlite3

from src.db.schema import create_schema
from src.db.similarity_repo import insert_similarity_pairs, list_similarity_pairs


def test_insert_and_list_similarity_pairs() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_similarity_pairs(
        conn,
        pairs=[("c1", "c2", 0.91, "name_only"), ("c2", "c3", 0.86, "name_summary")],
    )

    rows = list_similarity_pairs(conn)
    assert len(rows) == 2
    assert rows[0]["candidate_a_id"] == "c1"
