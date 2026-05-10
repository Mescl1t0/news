#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from common import ROOT, report_dir, today_str

TOOLS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = ["python3", str(TOOLS / script), *args]
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def print_ai_next_step(day: str) -> None:
    day_dir = report_dir(day)
    print("\nOpenClaw-native AI enrichment required:")
    print(f"1. Read:  {day_dir / 'ai_input.json'}")
    print(f"2. Write: {day_dir / 'ai_output.json'}")
    print("3. Return only item id, title_ru, description_ru.")
    print("4. Then run:")
    print(f"   python3 tools/build_report.py --date {day} --mode publish-ai")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--config", default=str(ROOT / "config" / "sections.json"))
    parser.add_argument(
        "--mode",
        choices=["full-fallback", "prepare-ai", "publish-ai"],
        default="full-fallback",
        help=(
            "full-fallback: fetch→normalize→deterministic fallback enrich→render; "
            "prepare-ai: fetch→normalize→make ai_input and stop for OpenClaw agent; "
            "publish-ai: merge ai_output→render→validate→archive"
        ),
    )
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--limit-override", type=int)
    parser.add_argument("--max-items-per-section", type=int, help="Trim normalized sections for test runs")
    args = parser.parse_args()

    shared = ["--date", args.date, "--config", args.config]

    if args.mode in {"full-fallback", "prepare-ai"}:
        if not args.skip_fetch:
            fetch_args = [*shared]
            if args.limit_override:
                fetch_args.extend(["--limit-override", str(args.limit_override)])
            run("fetch_selected.py", *fetch_args)
        normalize_args = [*shared]
        if args.max_items_per_section:
            normalize_args.extend(["--max-items-per-section", str(args.max_items_per_section)])
        run("normalize_report.py", *normalize_args)
        if args.mode == "prepare-ai":
            run("make_ai_input.py", "--date", args.date)

    if args.mode == "prepare-ai":
        print_ai_next_step(args.date)
        return

    if args.mode == "full-fallback":
        run("enrich_items.py", "--date", args.date)

    if args.mode == "publish-ai":
        ai_output_path = report_dir(args.date) / "ai_output.json"
        if not ai_output_path.exists():
            raise SystemExit(f"Missing ai_output.json: {ai_output_path}. Run prepare-ai and let OpenClaw agent write it first.")
        run("merge_ai_output.py", "--date", args.date)

    run("render_static_report.py", "--date", args.date)
    run("validate_report.py", *shared)
    run("update_archive.py", "--latest-date", args.date)


if __name__ == "__main__":
    main()
