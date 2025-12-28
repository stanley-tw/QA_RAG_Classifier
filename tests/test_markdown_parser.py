from src.pipeline.markdown_parser import parse_markdown


def test_parse_markdown_creates_heading_and_paragraph_blocks() -> None:
    md = "# Title\n\nIntro line one.\nIntro line two.\n\n## Section\nDetails here."
    blocks = parse_markdown(md)
    assert blocks[0].block_type == "heading"
    assert blocks[0].text == "Title"
    assert blocks[1].block_type == "paragraph"
    assert blocks[1].section_path == "Title"
    assert blocks[2].block_type == "heading"
    assert blocks[2].section_path == "Title > Section"
    assert blocks[3].block_type == "paragraph"
    assert blocks[3].section_path == "Title > Section"
