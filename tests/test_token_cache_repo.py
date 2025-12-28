import sqlite3

from src.db.schema import create_schema
from src.db.token_cache_repo import (
    get_token_count_cache,
    set_token_count_cache,
    get_trunc_text_cache,
    set_trunc_text_cache,
    get_token_count_cache_for_text,
    set_token_count_cache_for_text,
    get_trunc_text_cache_for_text,
    set_trunc_text_cache_for_text,
)


def test_token_count_cache_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    set_token_count_cache(
        conn, text_hash="h1", model_name="m1", token_count=12, tokenization_mode="exact"
    )
    row = get_token_count_cache(conn, text_hash="h1", model_name="m1")
    assert row["token_count"] == 12
    assert row["tokenization_mode"] == "exact"


def test_trunc_text_cache_roundtrip() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    set_trunc_text_cache(
        conn,
        text_hash="h2",
        model_name="m1",
        max_tokens=128,
        truncated_text="hello",
        tokenization_mode="approx",
    )
    row = get_trunc_text_cache(conn, text_hash="h2", model_name="m1", max_tokens=128)
    assert row["truncated_text"] == "hello"
    assert row["tokenization_mode"] == "approx"


def test_token_cache_helpers_use_text_hash() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    set_token_count_cache_for_text(
        conn,
        text="hello",
        model_name="m1",
        token_count=5,
        tokenization_mode="exact",
    )
    row = get_token_count_cache_for_text(conn, text="hello", model_name="m1")
    assert row["token_count"] == 5

    set_trunc_text_cache_for_text(
        conn,
        text="world",
        model_name="m1",
        max_tokens=3,
        truncated_text="wor",
        tokenization_mode="exact",
    )
    row = get_trunc_text_cache_for_text(conn, text="world", model_name="m1", max_tokens=3)
    assert row["truncated_text"] == "wor"
