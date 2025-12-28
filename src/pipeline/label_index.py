from __future__ import annotations

from typing import Dict, List


def build_label_index(
    embedding_model: str,
    embedding_dimension: int,
    domains: List[Dict[str, str]],
) -> Dict[str, object]:
    sorted_domains = sorted(domains, key=lambda d: d["domain_id"])
    return {
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dimension,
        "domain_ids": [d["domain_id"] for d in sorted_domains],
        "domain_display_names": [d["display_name"] for d in sorted_domains],
    }
