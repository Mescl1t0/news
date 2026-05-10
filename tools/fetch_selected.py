#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    BRIEFING_SCRIPT,
    FETCH_SCRIPT,
    PUBLIC_DIR,
    ROOT,
    ensure_dir,
    load_sections,
    now_iso,
    report_dir,
    run_json_command,
    today_str,
    write_json,
)


def fetch_section(section: dict, limit_override: int | None = None) -> dict:
    if section["fetch_mode"] == "source":
        limit = int(limit_override or section.get("default_limit") or 5)
        cmd = ["python3", str(FETCH_SCRIPT), "--source", section["source_key"], "--limit", str(limit), "--no-save"]
        data, stderr, returncode = run_json_command(cmd, ROOT)
        return {
            "id": section["id"],
            "title": section["title"],
            "type": section["type"],
            "fetch_mode": section["fetch_mode"],
            "source_key": section["source_key"],
            "requested_limit": limit,
            "returncode": returncode,
            "stderr": stderr,
            "raw": data or [],
        }
    profile = section["profile"]
    cmd = ["python3", str(BRIEFING_SCRIPT), "--profile", profile, "--no-save"]
    data, stderr, returncode = run_json_command(cmd, ROOT)
    return {
        "id": section["id"],
        "title": section["title"],
        "type": section["type"],
        "fetch_mode": section["fetch_mode"],
        "profile": profile,
        "returncode": returncode,
        "stderr": stderr,
        "raw": data or {},
    }



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--config", default=str(ROOT / "config" / "sections.json"))
    parser.add_argument("--out", default=None, help="Path to output raw.json")
    parser.add_argument("--limit-override", type=int)
    args = parser.parse_args()

    sections = load_sections(Path(args.config))
    day_dir = report_dir(args.date)
    ensure_dir(day_dir)
    out_path = Path(args.out) if args.out else day_dir / "raw.json"

    results = [fetch_section(section, args.limit_override) for section in sections]
    payload = {
        "date": args.date,
        "generated_at": now_iso(),
        "config": str(Path(args.config).resolve()),
        "sections": results,
    }
    write_json(out_path, payload)
    print(out_path)


if __name__ == "__main__":
    main()
