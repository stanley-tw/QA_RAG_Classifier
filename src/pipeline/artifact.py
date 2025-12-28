from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np


def write_artifact_bundle(
    output_dir: Path,
    artifact_version: str,
    embedding_model: str,
    embedding_provider: str,
    embedding_dimension: int,
    tokenization_mode: str,
    tokenization_fallback_allowed: bool,
    generation_config: Dict[str, Any],
    domains: List[Dict[str, Any]],
    label_index: Dict[str, Any],
    label_vec: np.ndarray,
    domain_repr: Optional[Iterable[Dict[str, Any]]] = None,
) -> None:
    _validate_artifact_inputs(domains, label_index, label_vec, embedding_model, embedding_dimension)
    output_dir.mkdir(parents=True, exist_ok=True)

    domains_path = output_dir / "domains.json"
    label_index_path = output_dir / "label_index.json"
    label_vec_path = output_dir / "label_vec.npy"
    domain_repr_path = output_dir / "domain_repr.jsonl"

    _write_json(domains_path, {"domains": domains})
    _write_json(label_index_path, label_index)
    np.save(label_vec_path, label_vec.astype(np.float32))

    files: Dict[str, str] = {
        "domains.json": _sha256(domains_path),
        "label_index.json": _sha256(label_index_path),
        "label_vec.npy": _sha256(label_vec_path),
    }

    if domain_repr is not None:
        _write_jsonl(domain_repr_path, domain_repr)
        files["domain_repr.jsonl"] = _sha256(domain_repr_path)

    manifest = {
        "artifact_version": artifact_version,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "embedding_model": embedding_model,
        "embedding_provider": embedding_provider,
        "embedding_dimension": embedding_dimension,
        "tokenization_policy": {
            "mode": tokenization_mode,
            "fallback_allowed": tokenization_fallback_allowed,
        },
        "domain_count": len(domains),
        "files": files,
        "generation_config": generation_config,
    }
    _write_json(output_dir / "artifact_manifest.json", manifest)


def _validate_artifact_inputs(
    domains: List[Dict[str, Any]],
    label_index: Dict[str, Any],
    label_vec: np.ndarray,
    embedding_model: str,
    embedding_dimension: int,
) -> None:
    domain_ids = label_index.get("domain_ids", [])
    if len(domain_ids) != len(domains):
        raise ValueError("label_index domain_ids length must match domains length")
    if label_vec.shape[0] != len(domain_ids):
        raise ValueError("label_vec row count must match label_index domain_ids length")
    if label_vec.shape[1] != embedding_dimension:
        raise ValueError("label_vec dimension must match embedding_dimension")
    if label_index.get("embedding_model") != embedding_model:
        raise ValueError("label_index embedding_model must match embedding_model")
    if label_index.get("embedding_dimension") != embedding_dimension:
        raise ValueError("label_index embedding_dimension must match embedding_dimension")


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
