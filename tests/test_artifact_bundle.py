from pathlib import Path
import json
import numpy as np

from src.pipeline.artifact import write_artifact_bundle


def test_write_artifact_bundle_creates_manifest_and_checksums(tmp_path: Path) -> None:
    output_dir = tmp_path / "domain_bundle_v1"
    domains = [
        {
            "domain_id": "domain_001",
            "display_name": "Auth",
            "aliases": ["Auth"],
            "source_pdfs": ["pdf_001"],
        }
    ]
    label_index = {
        "embedding_model": "text-embedding-3-small",
        "embedding_dimension": 3,
        "domain_ids": ["domain_001"],
        "domain_display_names": ["Auth"],
    }
    label_vec = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)

    write_artifact_bundle(
        output_dir=output_dir,
        artifact_version="v1",
        embedding_model="text-embedding-3-small",
        embedding_provider="azure_openai",
        embedding_dimension=3,
        tokenization_mode="exact",
        tokenization_fallback_allowed=True,
        generation_config={"merge_threshold_name_only": 0.9},
        domains=domains,
        label_index=label_index,
        label_vec=label_vec,
        domain_repr=None,
    )

    manifest_path = output_dir / "artifact_manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["domain_count"] == 1
    assert "domains.json" in manifest["files"]
    assert "label_vec.npy" in manifest["files"]
    assert manifest["files"]["label_vec.npy"].startswith("sha256:")
    assert manifest["files"]["domains.json"].startswith("sha256:")
    assert manifest["files"]["label_index.json"].startswith("sha256:")

    vec = np.load(output_dir / "label_vec.npy")
    assert vec.dtype == np.float32


def test_write_artifact_bundle_validates_inputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "domain_bundle_v1"
    domains = [{"domain_id": "domain_001"}]
    label_index = {
        "embedding_model": "text-embedding-3-small",
        "embedding_dimension": 3,
        "domain_ids": ["domain_001", "domain_002"],
        "domain_display_names": ["A", "B"],
    }
    label_vec = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)

    try:
        write_artifact_bundle(
            output_dir=output_dir,
            artifact_version="v1",
            embedding_model="text-embedding-3-small",
            embedding_provider="azure_openai",
            embedding_dimension=3,
            tokenization_mode="exact",
            tokenization_fallback_allowed=True,
            generation_config={},
            domains=domains,
            label_index=label_index,
            label_vec=label_vec,
            domain_repr=None,
        )
        assert False, "Expected ValueError"
    except ValueError:
        assert True
