from src.pipeline.merge import merge_candidates


def test_merge_excludes_rejected_pair() -> None:
    similarities = [("a", "b", 0.95, "name_only"), ("b", "c", 0.95, "name_only")]
    rejected = {("a", "b"), ("b", "a")}
    result = merge_candidates(
        similarities=similarities,
        thresholds_by_mode={"name_only": (0.9, 0.85)},
        rejected_pairs=rejected,
    )
    clusters = [set(cluster) for cluster in result.clusters]
    assert {"a"} in clusters
    assert {"b", "c"} in clusters


def test_review_items_collected_in_band() -> None:
    similarities = [("a", "b", 0.87, "name_only")]

    result = merge_candidates(
        similarities=similarities,
        thresholds_by_mode={"name_only": (0.9, 0.85)},
        rejected_pairs=set(),
    )

    assert len(result.review_items) == 1
    assert result.review_items[0].pair == ("a", "b")


def test_merge_creates_cluster() -> None:
    similarities = [("a", "b", 0.92, "name_only")]

    result = merge_candidates(
        similarities=similarities,
        thresholds_by_mode={"name_only": (0.9, 0.85)},
        rejected_pairs=set(),
    )

    assert result.clusters == [{"a", "b"}]
