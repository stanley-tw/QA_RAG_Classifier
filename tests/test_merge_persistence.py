import sqlite3
from datetime import datetime, timezone

from src.db.domain_repo import (
    list_block_domain_map,
    list_domain_aliases,
    list_domain_sources,
    list_domains,
)
from src.db.schema import create_schema
from src.db.similarity_repo import list_similarity_pairs
from src.db.review_repo import list_pending_reviews
from src.pipeline.candidates import DomainCandidate
from src.pipeline.merge_persist import persist_merge_results


def test_persist_merge_results_writes_review_and_similarity() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    candidates = {
        "c1": DomainCandidate(
            candidate_id="c1",
            candidate_name="Payments",
            normalized_name="payments",
            source_pdf_id="p1",
            source_block_id="b1",
            heading_level=1,
            representative_text="Payments",
        ),
        "c2": DomainCandidate(
            candidate_id="c2",
            candidate_name="Billing",
            normalized_name="billing",
            source_pdf_id="p1",
            source_block_id="b2",
            heading_level=2,
            representative_text="Billing",
        ),
    }
    persist_merge_results(
        conn=conn,
        clusters=[{"c1", "c2"}],
        candidates=candidates,
        review_items=[("c2", "c3", 0.87, "review_band")],
        persist_pairs=[("c1", "c2", 0.91, "name_only")],
        created_at=now,
        preferred_display_language="auto",
        min_review_threshold=0.85,
    )

    reviews = list_pending_reviews(conn)
    assert len(reviews) == 1

    similarities = list_similarity_pairs(conn)
    assert len(similarities) == 1


def test_persist_merge_results_creates_domains() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)

    now = datetime.now(timezone.utc).isoformat()
    candidates = {
        "c1": DomainCandidate(
            candidate_id="c1",
            candidate_name="Payments",
            normalized_name="payments",
            source_pdf_id="p1",
            source_block_id="b1",
            heading_level=1,
            representative_text="Payments",
        ),
        "c2": DomainCandidate(
            candidate_id="c2",
            candidate_name="Billing",
            normalized_name="billing",
            source_pdf_id="p2",
            source_block_id="b2",
            heading_level=2,
            representative_text="Billing",
        ),
    }
    persist_merge_results(
        conn=conn,
        clusters=[{"c1"}, {"c2"}],
        candidates=candidates,
        review_items=[],
        persist_pairs=[],
        created_at=now,
        preferred_display_language="auto",
        min_review_threshold=0.85,
    )

    domains = list_domains(conn)
    assert [d["domain_id"] for d in domains] == ["domain_001", "domain_002"]

    aliases = list_domain_aliases(conn)
    assert len(aliases) == 2

    sources = list_domain_sources(conn)
    assert len(sources) == 2

    mappings = list_block_domain_map(conn)
    assert len(mappings) == 2
