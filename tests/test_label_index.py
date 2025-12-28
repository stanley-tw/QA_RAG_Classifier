from src.pipeline.label_index import build_label_index


def test_build_label_index_sorts_domains_by_id() -> None:
    domains = [
        {"domain_id": "domain_010", "display_name": "Z"},
        {"domain_id": "domain_002", "display_name": "A"},
    ]
    index = build_label_index(
        embedding_model="text-embedding-3-small",
        embedding_dimension=3,
        domains=domains,
    )
    assert index["domain_ids"] == ["domain_002", "domain_010"]
