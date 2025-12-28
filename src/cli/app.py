from __future__ import annotations

import sqlite3

from rich.console import Console
from src.config import load_config
from src.db.schema import create_schema
from src.db.token_usage_repo import get_latest_run_usage, get_total_usage
from src.pipeline.run import run_pipeline


def run_cli(args: list[str]) -> int:
    console = Console()
    config = load_config()

    if not args or args[0] == "help":
        console.print("[bold]Domain Discovery CLI[/bold]")
        console.print("Usage:")
        console.print("  python src/main.py ui")
        console.print("  python src/main.py run")
        console.print("  python src/main.py help")
        console.print("")
        console.print("Current config:")
        console.print(f"  embedding_model: {config.embedding_model}")
        console.print(
            "  thresholds: "
            f"name_only={config.merge_threshold_name_only}/"
            f"{config.review_threshold_name_only}, "
            f"name_plus_summary={config.merge_threshold_name_plus_summary}/"
            f"{config.review_threshold_name_plus_summary}"
        )
        return 0

    if args[0] == "run":
        console.print("[bold]Running pipeline...[/bold]")
        success = run_pipeline(config)
        if success:
            console.print("[green]Pipeline run completed.[/green]")
            _print_token_usage(console, config.db_path)
            return 0
        console.print("[yellow]Pipeline run skipped (no PDFs or candidates).[/yellow]")
        return 1

    console.print(f"[red]Unknown command:[/red] {args[0]}")
    console.print("Use: python src/main.py help")
    return 1


def _print_token_usage(console: Console, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        latest = get_latest_run_usage(conn)
        totals = get_total_usage(conn)
        if not latest and not totals:
            console.print("[yellow]No token usage recorded yet.[/yellow]")
            return
        console.print("[bold]Token usage (latest run):[/bold]")
        if latest and latest.tokens_by_model:
            for model_name, total in latest.tokens_by_model.items():
                console.print(f"  {model_name}: {total}")
        else:
            console.print("  (no run usage available)")
        console.print("[bold]Token usage (cumulative):[/bold]")
        if totals:
            for model_name, total in totals.items():
                console.print(f"  {model_name}: {total}")
        else:
            console.print("  (no totals available)")
    finally:
        conn.close()
