import importlib
import sys
from types import ModuleType

from src.pipeline import tokenization


def test_approx_token_count_mixed_language() -> None:
    text = "ab銝剜?"
    original = tokenization._get_tiktoken_encoding
    try:
        tokenization._get_tiktoken_encoding = lambda _: (_ for _ in ()).throw(
            RuntimeError("no tiktoken")
        )
        result = tokenization.count_tokens(
            text, model_name="x", approx_enabled=True
        )
        assert result == 3  # 2/4 + 2 = 2.5 -> ceil to 3
    finally:
        tokenization._get_tiktoken_encoding = original


def test_approx_truncation_uses_safe_limit() -> None:
    text = "a" * 100
    original = tokenization._get_tiktoken_encoding
    try:
        tokenization._get_tiktoken_encoding = lambda _: (_ for _ in ()).throw(
            RuntimeError("no tiktoken")
        )
        truncated = tokenization.truncate_text(
            text, model_name="x", max_tokens=10, approx_enabled=True
        )
        assert len(truncated) <= 28  # 0.7 * 10 tokens -> 7 tokens -> 28 chars
    finally:
        tokenization._get_tiktoken_encoding = original


def test_exact_token_count_fallback_to_cl100k_base() -> None:
    original = sys.modules.get("tiktoken")
    fake = ModuleType("tiktoken")

    class FakeEncoding:
        def encode(self, text: str) -> list[int]:
            return list(range(len(text)))

        def decode(self, tokens: list[int]) -> str:
            return "x" * len(tokens)

    def encoding_for_model(_: str):
        raise KeyError("unknown model")

    def get_encoding(_: str):
        return FakeEncoding()

    fake.encoding_for_model = encoding_for_model
    fake.get_encoding = get_encoding

    sys.modules["tiktoken"] = fake
    importlib.reload(tokenization)
    try:
        count = tokenization.count_tokens(
            "abc", model_name="unknown", approx_enabled=False
        )
        assert count == 3
    finally:
        if original is not None:
            sys.modules["tiktoken"] = original
        else:
            sys.modules.pop("tiktoken", None)
        importlib.reload(tokenization)
