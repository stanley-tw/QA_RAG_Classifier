from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class BlockScore:
    block_id: str
    score: float
    text: str


def select_top_k_blocks(blocks: Sequence[BlockScore], k: int) -> List[BlockScore]:
    if k <= 0:
        return []
    return sorted(blocks, key=lambda b: b.score, reverse=True)[:k]
