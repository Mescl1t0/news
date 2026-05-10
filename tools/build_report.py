#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from common import ROOT, today_str

TOOLS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = ["python3", str(TOOLS / script), *args]
    subprocess.run(cmd, cwd=str(ROOT), check=True)



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--config", default=str(ROOT / "config" / "sections.json"))
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--limit-override", type=int)
    args = parser.parse_args()

    shared = ["--date", args.date, "--config", args.config]
    if not args.skip_fetch:
        fetch_args = [*shared]
        if args.limit_override:
            fetch_args.extend(["--limit-override", str(args.limit_override)])
        run("fetch_selected.py", *fetch_args)
    run("normalize_report.py", *shared)
    run("enrich_items.py", "--date", args.date)
    run("render_static_report.py", "--date", args.date)
    run("validate_report.py", *shared)
    run("update_archive.py", "--latest-date", args.date)


if __name__ == "__main__":
    main()
