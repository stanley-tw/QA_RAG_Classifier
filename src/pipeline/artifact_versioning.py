from __future__ import annotations

from pathlib import Path


def next_bundle_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    existing = []
    for child in root.iterdir():
        if child.is_dir() and child.name.startswith("domain_bundle_v"):
            suffix = child.name.replace("domain_bundle_v", "")
            if suffix.isdigit():
                existing.append(int(suffix))
    next_version = max(existing, default=0) + 1
    return root / f"domain_bundle_v{next_version}"
