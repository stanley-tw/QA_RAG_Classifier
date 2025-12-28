from src.pipeline.candidates import ContentBlock, extract_candidates, normalize_name


def test_normalize_name_strips_markers_and_case() -> None:
    assert normalize_name("Domain: Payments ") == "payments"
    assert normalize_name(" MODULE - Risk ") == "risk"


def test_extract_candidates_from_heading() -> None:
    blocks = [
        ContentBlock(
            block_id="b1",
            pdf_id="p1",
            section_path="1",
            heading_level=1,
            block_type="heading",
            text="Payments System",
            page_index=1,
            position_index=1,
        )
    ]
    candidates = extract_candidates(blocks)
    assert len(candidates) == 1
    assert candidates[0].candidate_name == "Payments System"
    assert candidates[0].normalized_name == "payments system"


def test_extract_candidates_from_paragraph_marker() -> None:
    blocks = [
        ContentBlock(
            block_id="b2",
            pdf_id="p1",
            section_path="1.1",
            heading_level=3,
            block_type="paragraph",
            text="Domain: Fraud Detection",
            page_index=2,
            position_index=5,
        )
    ]
    candidates = extract_candidates(blocks)
    assert len(candidates) == 1
    assert candidates[0].candidate_name == "Fraud Detection"
