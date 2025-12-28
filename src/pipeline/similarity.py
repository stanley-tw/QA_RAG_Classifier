from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


def generate_candidate_pairs(
    candidate_ids: Iterable[str],
    normalized_names: Dict[str, str],
    prefix_len: int = 4,
    length_window: int = 6,
) -> List[Tuple[str, str]]:
    buckets: Dict[str, List[Tuple[str, int]]] = {}
    for cid in candidate_ids:
        name = normalized_names.get(cid, "")
        key = name[:prefix_len]
        buckets.setdefault(key, []).append((cid, len(name)))

    pairs: List[Tuple[str, str]] = []
    for items in buckets.values():
        items.sort(key=lambda item: item[1])
        for i in range(len(items)):
            a_id, a_len = items[i]
            for j in range(i + 1, len(items)):
                b_id, b_len = items[j]
                if b_len - a_len > length_window:
                    break
                pairs.append((a_id, b_id))
    return pairs


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    vec_a = np.array(a, dtype=np.float32)
    vec_b = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


def similarity_pairs_for_mode(
    pairs: Iterable[Tuple[str, str]],
    embeddings: Dict[str, Sequence[float]],
    mode: str,
) -> List[Tuple[str, str, float, str]]:
    results: List[Tuple[str, str, float, str]] = []
    for a, b in pairs:
        if a not in embeddings or b not in embeddings:
            continue
        score = cosine_similarity(embeddings[a], embeddings[b])
        results.append((a, b, score, mode))
    return results
