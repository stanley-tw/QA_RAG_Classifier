from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli.app import run_cli


def run_ui() -> int:
    app_path = Path(__file__).parent / "ui" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 0


def rag() -> int:
    return run_ui()


def main() -> int:
    args = sys.argv[1:]

    if args and args[0] == "ui":
        return run_ui()

    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
