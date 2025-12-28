from __future__ import annotations

import sqlite3


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS pdfs(
          pdf_id TEXT PRIMARY KEY,
          file_path TEXT NOT NULL,
          checksum TEXT NOT NULL,
          ingested_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS content_blocks(
          block_id TEXT PRIMARY KEY,
          pdf_id TEXT NOT NULL,
          section_path TEXT,
          heading_level INTEGER,
          block_type TEXT NOT NULL,
          text TEXT NOT NULL,
          page_index INTEGER,
          position_index INTEGER,
          FOREIGN KEY(pdf_id) REFERENCES pdfs(pdf_id)
        );

        CREATE TABLE IF NOT EXISTS domain_candidates(
          candidate_id TEXT PRIMARY KEY,
          candidate_name TEXT NOT NULL,
          normalized_name TEXT NOT NULL,
          source_pdf_id TEXT NOT NULL,
          source_block_id TEXT NOT NULL,
          heading_level INTEGER,
          representative_text TEXT NOT NULL,
          FOREIGN KEY(source_pdf_id) REFERENCES pdfs(pdf_id),
          FOREIGN KEY(source_block_id) REFERENCES content_blocks(block_id)
        );

        CREATE TABLE IF NOT EXISTS candidate_embeddings(
          candidate_id TEXT PRIMARY KEY,
          model_name TEXT NOT NULL,
          vector TEXT NOT NULL,
          token_count INTEGER NOT NULL,
          tokenization_mode TEXT NOT NULL,
          FOREIGN KEY(candidate_id) REFERENCES domain_candidates(candidate_id)
        );

        CREATE TABLE IF NOT EXISTS candidate_similarity(
          candidate_a_id TEXT NOT NULL,
          candidate_b_id TEXT NOT NULL,
          similarity REAL NOT NULL,
          mode TEXT NOT NULL,
          PRIMARY KEY(candidate_a_id, candidate_b_id),
          FOREIGN KEY(candidate_a_id) REFERENCES domain_candidates(candidate_id),
          FOREIGN KEY(candidate_b_id) REFERENCES domain_candidates(candidate_id)
        );

        CREATE TABLE IF NOT EXISTS review_queue(
          review_id TEXT PRIMARY KEY,
          candidate_a_id TEXT NOT NULL,
          candidate_b_id TEXT NOT NULL,
          similarity REAL NOT NULL,
          reason TEXT NOT NULL,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL,
          resolved_at TEXT,
          FOREIGN KEY(candidate_a_id) REFERENCES domain_candidates(candidate_id),
          FOREIGN KEY(candidate_b_id) REFERENCES domain_candidates(candidate_id)
        );

        CREATE TABLE IF NOT EXISTS domains(
          domain_id TEXT PRIMARY KEY,
          display_name TEXT NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS domain_aliases(
          domain_id TEXT NOT NULL,
          alias TEXT NOT NULL,
          source_pdf_id TEXT NOT NULL,
          heading_level INTEGER,
          PRIMARY KEY(domain_id, alias, source_pdf_id),
          FOREIGN KEY(domain_id) REFERENCES domains(domain_id),
          FOREIGN KEY(source_pdf_id) REFERENCES pdfs(pdf_id)
        );

        CREATE TABLE IF NOT EXISTS domain_sources(
          domain_id TEXT NOT NULL,
          pdf_id TEXT NOT NULL,
          PRIMARY KEY(domain_id, pdf_id),
          FOREIGN KEY(domain_id) REFERENCES domains(domain_id),
          FOREIGN KEY(pdf_id) REFERENCES pdfs(pdf_id)
        );

        CREATE TABLE IF NOT EXISTS domain_embeddings(
          domain_id TEXT PRIMARY KEY,
          model_name TEXT NOT NULL,
          vector TEXT NOT NULL,
          token_count INTEGER NOT NULL,
          tokenization_mode TEXT NOT NULL,
          FOREIGN KEY(domain_id) REFERENCES domains(domain_id)
        );

        CREATE TABLE IF NOT EXISTS block_domain_map(
          block_id TEXT NOT NULL,
          domain_id TEXT NOT NULL,
          PRIMARY KEY(block_id, domain_id),
          FOREIGN KEY(block_id) REFERENCES content_blocks(block_id),
          FOREIGN KEY(domain_id) REFERENCES domains(domain_id)
        );

        CREATE TABLE IF NOT EXISTS token_count_cache(
          text_hash TEXT NOT NULL,
          model_name TEXT NOT NULL,
          token_count INTEGER NOT NULL,
          tokenization_mode TEXT NOT NULL,
          PRIMARY KEY(text_hash, model_name)
        );

        CREATE TABLE IF NOT EXISTS trunc_text_cache(
          text_hash TEXT NOT NULL,
          model_name TEXT NOT NULL,
          max_tokens INTEGER NOT NULL,
          truncated_text TEXT NOT NULL,
          tokenization_mode TEXT NOT NULL,
          PRIMARY KEY(text_hash, model_name, max_tokens)
        );

        CREATE INDEX IF NOT EXISTS idx_content_blocks_pdf_id ON content_blocks(pdf_id);
        CREATE INDEX IF NOT EXISTS idx_candidates_pdf_id ON domain_candidates(source_pdf_id);
        CREATE INDEX IF NOT EXISTS idx_candidates_norm_name ON domain_candidates(normalized_name);
        CREATE INDEX IF NOT EXISTS idx_candidate_similarity_mode ON candidate_similarity(mode);
        CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
        CREATE INDEX IF NOT EXISTS idx_domain_aliases_domain_id ON domain_aliases(domain_id);
        CREATE INDEX IF NOT EXISTS idx_domain_sources_domain_id ON domain_sources(domain_id);
        """
    )
