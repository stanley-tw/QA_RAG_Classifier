# UI Specification

## Purpose
Provide a minimal Streamlit UI to upload PDFs, adjust parameters, trigger the RAG pipeline, and view discovered domains.

## Pages
- Single-page layout.

## Sections
1. Upload PDFs
2. Stored PDFs list and Processed PDFs list
3. Parameters and Run button
4. Domain list

## Functional Requirements
- Upload multiple PDF files.
- Show two lists:
  - Stored PDFs (ingested or staged).
  - Processed PDFs (successfully parsed).
- Parameter controls:
  - Embedding model selection.
  - Merge/review thresholds.
  - Preferred display language.
- Button to start the RAG pipeline run.
- Disable Run button while a pipeline run is in progress to prevent double-triggering and session_state races.
- Domain list view:
  - Display domain_id and display_name.
  - Show aliases and source PDFs when available.
  - After a successful run, reload the domain list from SQLite.
- Provide a link to the artifact bundle output location (see `docs/artifact_spec.md`).
 - Display the configured artifact output directory from `ARTIFACT_DIR`.
- Display token usage for the most recent run and cumulative total by model.

## UI State
Use `st.session_state` for:
- `stored_pdfs`
- `processed_pdfs`
- `domain_list`

## Non-Functional
- No pipeline execution logic in UI layer.
- UI must call into pipeline service functions when wired.
