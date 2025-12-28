from src.pipeline.representation import BlockScore, select_top_k_blocks


def test_select_top_k_blocks() -> None:
    blocks = [
        BlockScore(block_id="b1", score=0.2, text="a"),
        BlockScore(block_id="b2", score=0.9, text="b"),
        BlockScore(block_id="b3", score=0.5, text="c"),
    ]
    selected = select_top_k_blocks(blocks, k=2)
    assert [b.block_id for b in selected] == ["b2", "b3"]
