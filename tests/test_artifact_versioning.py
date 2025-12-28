from pathlib import Path

from src.pipeline.artifact_versioning import next_bundle_dir


def test_next_bundle_dir_increments(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    (root / "domain_bundle_v1").mkdir(parents=True)
    (root / "domain_bundle_v2").mkdir()
    next_dir = next_bundle_dir(root)
    assert next_dir.name == "domain_bundle_v3"
