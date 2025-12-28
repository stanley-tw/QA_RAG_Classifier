from src.pipeline.hash_utils import text_hash


def test_text_hash_is_stable() -> None:
    assert text_hash("abc") == text_hash("abc")
    assert text_hash("abc") != text_hash("abcd")
