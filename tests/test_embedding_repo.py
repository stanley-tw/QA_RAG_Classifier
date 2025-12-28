import sqlite3

from src.db.embedding_repo import (
    insert_candidate_embedding,
    insert_domain_embedding,
    insert_candidate_embedding_vector,
    insert_domain_embedding_vector,
    list_candidate_embeddings,
    list_domain_embeddings,
    parse_vector,
)
from src.db.schema import create_schema


def test_candidate_embedding_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_candidate_embedding(
        conn,
        candidate_id="c1",
        model_name="m1",
        vector="[0.1,0.2]",
        token_count=2,
        tokenization_mode="exact",
    )
    rows = list_candidate_embeddings(conn)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "c1"


def test_domain_embedding_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_domain_embedding(
        conn,
        domain_id="d1",
        model_name="m1",
        vector="[0.2,0.3]",
        token_count=2,
        tokenization_mode="exact",
    )
    rows = list_domain_embeddings(conn)
    assert len(rows) == 1
    assert rows[0]["domain_id"] == "d1"


def test_embedding_vector_helpers_serialize_json() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    insert_candidate_embedding_vector(
        conn,
        candidate_id="c2",
        model_name="m2",
        vector=[0.1, 0.2],
        token_count=2,
        tokenization_mode="exact",
    )
    rows = list_candidate_embeddings(conn)
    assert parse_vector(rows[0]["vector"]) == [0.1, 0.2]


def test_insert_embedding_rejects_non_json() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    try:
        insert_domain_embedding(
            conn,
            domain_id="d2",
            model_name="m1",
            vector="not-json",
            token_count=2,
            tokenization_mode="exact",
        )
        assert False, "Expected ValueError"
    except ValueError:
        assert True
