# QA RAG Classifier

## Goal
Build a deterministic pipeline that ingests PDFs, discovers canonical domains, and produces embeddings for downstream classification.

## What It Does
- Parse PDFs into structured content blocks (MinerU or Docling via RAG-Anything).
- Extract and merge domain candidates into canonical domains.
- Generate embeddings with Azure OpenAI.
- Persist everything in SQLite and export a versioned artifact bundle.

## Requirements
- Python 3.13.x
- uv
- Azure OpenAI credentials

## Installation
1) Clone the repo and submodules
```bash
git clone <repo_url>
cd QA_RAG_Classifier
git submodule update --init --recursive
```

2) Create and sync the environment
```bash
uv sync
```

3) Set Azure OpenAI credentials
```bash
# Required
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<your-key>"

# Optional (default: 2024-02-15-preview)
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```
On Windows PowerShell:
```powershell
$env:AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY="<your-key>"
$env:AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

## Usage
### UI
```bash
uv run rag
```
This runs the Streamlit UI.

### CLI
```bash
uv run src/main.py run
```
This runs one pipeline pass using current configuration.

### Config
All config is driven by environment variables (defaults shown):
- `DB_PATH=./data/app.db`
- `PDF_STORAGE_DIR=./data/pdfs`
- `RAG_PARSER=mineru`
- `RAG_PARSE_METHOD=auto`
- `RAG_OUTPUT_DIR=./data/rag_output`
- `ARTIFACT_DIR=./artifacts`
- `EMBEDDING_MODEL=text-embedding-3-small`

## Output
- SQLite DB at `DB_PATH`
- Artifact bundle under `ARTIFACT_DIR` (see `docs/artifact_spec.md`)

## Notes
- First run may download MinerU models from Hugging Face. This can take time.
- On Windows, enabling Developer Mode allows symlink caching for faster downloads.
- Token usage is recorded per run and per model in SQLite and shown in UI/CLI.

## Tests
```bash
uv run pytest
```
