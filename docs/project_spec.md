
# Project Specification: Canonical Domain Discovery and Embedding Pipeline

## Purpose
Build a system that ingests multiple PDF documents, discovers domain labels, merges semantically equivalent domains, and produces a canonical domain list with one embedding vector per domain. The pipeline must use RAG-Anything for document ingestion and parsing and must remain deterministic, explainable, and stable across reruns.

## Scope
- Ingest 10-20 PDFs (each may be hundreds of pages).
- Extract structured content and candidate domain labels.
- Normalize and merge domain candidates across PDFs.
- Generate one embedding vector per canonical domain.
- Persist all outputs and intermediate artifacts in SQLite.
- Expose CLI/UI controls for model selection, thresholds, run, and review.

## Non-Goals
- No fixed taxonomy.
- No manual labeling as a prerequisite.
- No modification of the RAG-Anything source code under `DO_NOT_READ/`.

## Tech Constraints
- Python 3.13+ and `uv` are mandatory.
- Embeddings must use Azure OpenAI `AzureOpenAI` client.
- Token counting must use `tiktoken` encoding for the selected embedding model.
- Approximate tokenization is allowed only as a fallback and must be flagged as such.

## High-Level Pipeline
1. **Ingest PDFs with RAG-Anything**
2. **Extract Content Blocks**
3. **Domain Candidate Extraction**
4. **Candidate Normalization**
5. **Candidate Embedding + Similarity**
6. **Canonical Domain Merging**
7. **Canonical Name Selection**
8. **Domain Embedding Generation**
9. **Persistence + Reporting**

## Inputs
- `pdf_files`: list of PDF paths

## Outputs
- Canonical domain list with metadata
- Domain embedding dictionary (`domain_id -> embedding_vector`)
- Mapping tables:
  - PDF -> domains
  - content block -> domain
- Review queue for ambiguous merges
- Artifact bundle for downstream consumers (see `docs/artifact_spec.md`)

## Data Model (Logical)

### Content Block
```
ContentBlock {
  block_id: str,
  pdf_id: str,
  section_path: str,          # e.g., "1.2 > 1.2.1"
  heading_level: int,         # 1=H1, 2=H2, ...
  block_type: str,            # heading | paragraph | table | figure | equation
  text: str,
  page_index: int,
  position_index: int
}
```

### Domain Candidate
```
DomainCandidate {
  candidate_id: str,
  candidate_name: str,
  normalized_name: str,
  source_pdf_id: str,
  source_block_id: str,
  heading_level: int,
  representative_text: str
}
```

### Canonical Domain
```
Domain {
  domain_id: str,             # domain_001, domain_002, ...
  display_name: str,
  aliases: List[str],
  source_pdfs: List[str]
}
```

### Review Queue Item
```
ReviewItem {
  review_id: str,
  candidate_a_id: str,
  candidate_b_id: str,
  similarity: float,
  reason: str,
  status: str                # pending | approved | rejected
}
```

## RAG-Anything Ingestion
- Use RAG-Anything to parse PDFs into structured blocks.
- Must preserve headings and hierarchy.
- Persist block-level metadata for later aggregation.

## Candidate Extraction Rules
Identify candidate domains using:
- Section or subsection titles.
- Explicit markers like "Domain:", "Subsystem:", "Module:".
- High-level headings with semantic weight.

Representative text should include:
- The heading text.
- 3-10 nearby sentences or key paragraphs where available.

## Normalization Rules
- Case folding.
- Strip formatting artifacts.
- Remove known prefixes/suffixes (e.g., "Domain:", "Module:").
- Trim whitespace and punctuation.

## Embedding and Similarity

### Embedding Models
- Supported: `text-embedding-3-small` (default), `text-embedding-3-large`.
- Selection via `src/config.py`, CLI, and UI.

### Token Counting and Truncation
- Use `tiktoken.encoding_for_model(EMBED_MODEL)`.
- If model is unknown to `tiktoken`, fallback to `tiktoken.get_encoding("cl100k_base")`.

### Token Cache (SQLite)
Store:
- `token_count_cache`: `hash(text) + model_name -> token_count`
- `trunc_text_cache`: `hash(text) + model_name + max_tokens -> truncated_text`

### Approximate Tokenization (Fallback Only)
Approx mode is allowed only when:
- `tiktoken` is unavailable by design.
- Cost estimation is sufficient (not exact truncation).
- Pipeline needs to continue after tokenizer failure.

Approx rule:
- `approx_tokens = ascii_chars / 4 + non_ascii_chars * 1.0`
- In approx mode, use `0.7 * MAX_TOKENS` as the effective truncation limit.
- Persist a `tokenization_mode` flag (`exact` or `approx`) with each cache entry.

### Similarity Thresholds
Two matching modes are required:

1) Name-only (candidate name or short representative text)
- Merge threshold: 0.90
- Review threshold: 0.85 to 0.90 (inclusive lower bound)

2) Name + summary (name plus 3-10 sentences summary/snippets)
- Merge threshold: 0.86
- Review threshold: 0.82 to 0.86 (inclusive lower bound)

Thresholds must be configurable in `src/config.py` and editable via CLI/UI.

## Canonical Domain Merging

### Candidate Embedding
- Generate embeddings for each candidate's representative text.
- Use cosine similarity as the primary signal.
- All merging must be deterministic and reproducible.

### Merge Algorithm (Deterministic)
1. Compute pairwise similarities within a manageable window (index candidates by normalized name prefix and length to reduce comparisons). Do not do full O(N^2).
2. If similarity >= merge threshold, create an edge between candidates.
3. If similarity is within the review threshold band, create a review queue item.
4. Build connected components via union-find; each component is a domain cluster.

### Review Queue
- Items include: candidate pair, similarity score, and reason (e.g., "Name-only similarity in review band").
- Review decisions must be persisted as approved or rejected.
- Approved pairs are merged; rejected pairs remain separate even if similar.
- Rejected pairs must be excluded before union-find (hard constraint).

## Canonical Domain ID and Display Name

### Canonical ID
- `domain_001`, `domain_002`, ... assigned in deterministic order:
  - Sort clusters by the smallest candidate_id (lexicographic).
  - Assign IDs in that order.
- IDs must never depend on LLM output.

### Display Name (Rules First)
Select display name from aliases with this priority:
1. Highest frequency across PDFs.
2. Higher heading level (H1 > H2 > H3 > paragraph).
3. Shorter, higher information density name.
4. Preserve original language (prefer all-English if tie remains).

### LLM Fallback for Display Name
Only allowed if:
- Aliases are highly divergent, or
- Aliases are low-signal (e.g., "Overview", "Introduction").

If used:
- Input: aliases + top representative snippets + desired language.
- Output JSON only:
  ```
  {"display_name": "...", "summary": "...", "keywords": ["..."]}
  ```
- Use `temperature=0`.
- Must not invent concepts not supported by aliases/snippets.

## Domain Embedding Generation
For each canonical domain:
1. Aggregate all content blocks mapped to that domain.
2. Build a representation text using:
   - Selected display name
   - Top headings
   - Key paragraphs or summaries
3. Optional strategy (non-mandatory, for large domains):
   - Top-K blocks by TF-IDF/centrality, or
   - Per-block embeddings then centroid.
4. Truncate to model max tokens using exact tokenizer or approx mode if required.
5. Generate a single embedding vector:
   - `label_vec[domain_id] = embedding(domain_representation_text)`

## Mappings
- PDF -> domains (many-to-many).
- Content block -> domain (many-to-one, default).
- Candidate -> domain (many-to-one).

## Persistence (SQLite Schema)
Required tables (logical):
- `pdfs(pdf_id, file_path, checksum, ingested_at)`
- `content_blocks(block_id, pdf_id, section_path, heading_level, block_type, text, page_index, position_index)`
- `domain_candidates(candidate_id, candidate_name, normalized_name, source_pdf_id, source_block_id, heading_level, representative_text)`
- `candidate_embeddings(candidate_id, model_name, vector, token_count, tokenization_mode)`
- `candidate_similarity(candidate_a_id, candidate_b_id, similarity, mode)`
- `review_queue(review_id, candidate_a_id, candidate_b_id, similarity, reason, status, created_at, resolved_at)`
- `domains(domain_id, display_name, created_at)`
- `domain_aliases(domain_id, alias, source_pdf_id, heading_level)`
- `domain_sources(domain_id, pdf_id)`
- `domain_embeddings(domain_id, model_name, vector, token_count, tokenization_mode)`
- `block_domain_map(block_id, domain_id)`
- `token_count_cache(text_hash, model_name, token_count, tokenization_mode)`
- `trunc_text_cache(text_hash, model_name, max_tokens, truncated_text, tokenization_mode)`

## Configuration (src/config.py)
Must expose:
- `EMBEDDING_MODEL` (default `text-embedding-3-small`)
- `EMBEDDING_MODEL_OPTIONS` (small, large)
- `MERGE_THRESHOLD_NAME_ONLY`
- `REVIEW_THRESHOLD_NAME_ONLY`
- `MERGE_THRESHOLD_NAME_PLUS_SUMMARY`
- `REVIEW_THRESHOLD_NAME_PLUS_SUMMARY`
- `MAX_TOKENS_PER_EMBED`
- `TOKENIZATION_FALLBACK_APPROX_ENABLED`
- `DB_PATH`
- `ARTIFACT_DIR`
- `PREFERRED_DISPLAY_LANGUAGE` (auto | en | zh)

All of the above must be editable via CLI/UI.

## CLI/UI Requirements
Minimal actions:
- Select embedding model (small/large).
- Adjust thresholds (merge and review).
- Trigger PDF ingestion and parsing.
- View canonical domains and aliases.
- Review queue: approve/reject candidate merges.

## Azure OpenAI Integration
- Use the new `AzureOpenAI` client.
- Follow Azure environment variable conventions for endpoint and key.
- Deployment name for embeddings must be configurable.

## Determinism and Explainability
- All merges must be reproducible with the same inputs and config.
- Store similarity scores and merge decisions.
- Prefer rule-based naming; LLM is a last resort with fixed output schema.

## Failure Handling
- If tiktoken fails, use approx mode and persist tokenization mode.
- If embeddings fail for a candidate, mark and continue processing others.
- If RAG-Anything parse fails for a file, log and continue; record failure.
- Do not persist full pairwise similarity. Persist only:
  - similarity >= min(review_threshold), or
  - pairs that are placed into the review queue.
- Add indexes on `candidate_similarity(candidate_a_id, candidate_b_id)` and `review_queue(status)`.
