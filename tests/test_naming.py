from src.pipeline.naming import (
    AliasInfo,
    build_llm_naming_request,
    select_display_name,
    should_use_llm_fallback,
)


def test_select_display_name_prefers_frequency_then_heading() -> None:
    aliases = [
        AliasInfo(alias="Payments", source_pdf_id="p1", heading_level=2),
        AliasInfo(alias="Payments", source_pdf_id="p2", heading_level=3),
        AliasInfo(alias="Billing", source_pdf_id="p1", heading_level=1),
    ]
    assert select_display_name(aliases, preferred_language="auto") == "Payments"


def test_select_display_name_prefers_english_on_tie_auto() -> None:
    aliases = [
        AliasInfo(alias="登录", source_pdf_id="p1", heading_level=1),
        AliasInfo(alias="Login", source_pdf_id="p1", heading_level=1),
    ]
    assert select_display_name(aliases, preferred_language="auto") == "Login"


def test_should_use_llm_fallback_for_low_signal_aliases() -> None:
    assert should_use_llm_fallback(["Overview", "Introduction"]) is True


def test_should_use_llm_fallback_for_divergent_aliases() -> None:
    assert should_use_llm_fallback(["Payments", "Machine Learning"]) is True


def test_llm_request_contains_schema() -> None:
    request = build_llm_naming_request(["Auth"], ["Auth handles login"], "en")
    assert "output_schema" in request
