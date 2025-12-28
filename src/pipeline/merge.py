from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set, Tuple


@dataclass(frozen=True)
class ReviewItem:
    pair: Tuple[str, str]
    similarity: float
    reason: str


@dataclass(frozen=True)
class MergeResult:
    clusters: List[Set[str]]
    review_items: List[ReviewItem]
    persist_pairs: List[Tuple[str, str, float, str]]


class _UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self._parent[item]
        if parent != item:
            self._parent[item] = self.find(parent)
        return self._parent[item]

    def union(self, a: str, b: str) -> None:
        parent_a = self.find(a)
        parent_b = self.find(b)
        if parent_a != parent_b:
            self._parent[parent_b] = parent_a

    def clusters(self) -> List[Set[str]]:
        clusters: dict[str, Set[str]] = {}
        for item in self._parent:
            root = self.find(item)
            clusters.setdefault(root, set()).add(item)
        return list(clusters.values())


def merge_candidates(
    similarities: Sequence[Tuple[str, str, float, str]],
    thresholds_by_mode: dict[str, Tuple[float, float]],
    rejected_pairs: Set[Tuple[str, str]],
    items: Iterable[str] | None = None,
) -> MergeResult:
    base_items = set(items) if items is not None else set()
    similarity_items = {a for pair in similarities for a in pair[:2]}
    all_items = base_items | similarity_items
    items_list = sorted(all_items)
    union_find = _UnionFind(items_list)
    review_items: List[ReviewItem] = []
    persist_pairs: List[Tuple[str, str, float, str]] = []

    for a, b, score, mode in similarities:
        if mode not in thresholds_by_mode:
            raise ValueError(f"Missing thresholds for mode: {mode}")
        merge_threshold, review_threshold = thresholds_by_mode[mode]
        if (a, b) in rejected_pairs or (b, a) in rejected_pairs:
            continue

        if score >= review_threshold:
            persist_pairs.append((a, b, score, mode))

        if score >= merge_threshold:
            union_find.union(a, b)
        elif review_threshold <= score < merge_threshold:
            review_items.append(
                ReviewItem(
                    pair=(a, b),
                    similarity=score,
                    reason=f"{mode}_review_band",
                )
            )

    clusters = union_find.clusters()
    return MergeResult(
        clusters=clusters, review_items=review_items, persist_pairs=persist_pairs
    )
