---
name: consuming-domain-artifacts
description: Consumes domain artifact bundles produced by QA_RAG_Classifier, validates artifact_manifest.json integrity and compatibility, loads label_vec.npy + label_index.json, and maps domain_ids to display names. Use when a project needs to load domain_bundle_v* outputs, validate checksums, enforce embedding model/dimension matching, or run downstream domain classification without accessing the source SQLite database.
---

# Consume domain artifact bundles

## Validate the bundle first
- Read `artifact_manifest.json` before anything else.
- Fail fast if any required keys are missing:
  - `artifact_version`, `created_at`, `embedding_model`, `embedding_provider`,
    `embedding_dimension`, `tokenization_policy`, `domain_count`, `files`,
    `generation_config`.
- Verify file presence for the minimum set:
  - `artifact_manifest.json`, `domains.json`, `label_index.json`, `label_vec.npy`.
- Verify SHA-256 checksums in `artifact_manifest.json.files` for every listed file.
- Reject bundles if:
  - `embedding_model` does not match the model your project will use for query embeddings.
  - `embedding_dimension` does not match the loaded `label_vec.npy` second dimension.
  - `label_index.embedding_model` or `label_index.embedding_dimension` disagree with the manifest.
  - `domain_count` does not match the number of rows in `label_vec.npy`.

## Load and map artifacts
- `label_index.json` is the authoritative ordering:
  - `domain_ids[i]` corresponds to `label_vec[i]`.
  - Do not reorder domains.
- `domains.json` provides display metadata:
  - Map by `domain_id` to show `display_name`, `aliases`, and `source_pdfs`.
- `domain_repr.jsonl` is optional:
  - Load only if present; use for explainability/debugging.

## Data integrity checks (required)
- Ensure `label_vec.npy` dtype is float32 and shape `(N, D)`.
- Ensure `N == len(label_index.domain_ids) == domain_count`.
- Ensure `D == embedding_dimension`.
- Ensure `label_index.domain_display_names` length matches `domain_ids`.

## Usage expectations
- Treat the bundle as immutable input.
- Do not require access to the source SQLite database.
- Use cosine similarity for scoring; normalization is handled downstream.

## Error handling
- If any validation fails, stop and return a clear error that names the failed check.
- Never guess or auto-fix mismatched metadata or dimensions.
