# Design Specification

## Goals
- Deterministic domain discovery and merging.
- Configurable thresholds and embedding model selection.
- SQLite persistence for all artifacts.

## Modules
- `src/main.py`: CLI/UI entrypoint.
- `src/cli/app.py`: CLI commands and help.
- `src/ui/app.py`: Streamlit UI rendering only.
- `src/config.py`: Configuration loader.
- `src/db/`: SQLite access layer (to be implemented).
- `src/pipeline/`: Pipeline modules must be pure and side-effect free, except through the DB access layer.
- Artifact bundle writer (see `docs/artifact_spec.md`).

## Key Flows
1. CLI and UI must use the same config loading path and schema.
2. Pipeline ingests PDFs using RAG-Anything.
3. Candidate extraction and normalization.
4. Candidate embedding and similarity filtering.
5. Canonical domain formation and naming.
6. Domain embeddings generation.
7. Persist outputs into SQLite.

## Configuration
Required fields:
- `EMBEDDING_MODEL`
- `MERGE_THRESHOLD_NAME_ONLY`
- `REVIEW_THRESHOLD_NAME_ONLY`
- `MERGE_THRESHOLD_NAME_PLUS_SUMMARY`
- `REVIEW_THRESHOLD_NAME_PLUS_SUMMARY`
- `MAX_TOKENS_PER_EMBED`
- `TOKENIZATION_FALLBACK_APPROX_ENABLED`
- `PREFERRED_DISPLAY_LANGUAGE`
- `DB_PATH`
- `ARTIFACT_DIR`

## Error Handling
- Keep pipeline running when a single PDF fails.
- Record failures in SQLite.
