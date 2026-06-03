#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import time

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

RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2


def raw_item_count(section: dict, raw: object) -> int:
    if section["type"] == "digest":
        if not isinstance(raw, dict):
            return 0
        return sum(len(items or []) for items in raw.values())
    if not isinstance(raw, list):
        return 0
    return len(raw)


def should_retry(section: dict, result: dict) -> bool:
    if section.get("allow_empty", False):
        return False
    if result.get("returncode") != 0:
        return True
    return raw_item_count(section, result.get("raw")) == 0


def annotate_retry(result: dict, attempt: int) -> None:
    note = f"[retry {attempt}/{RETRY_ATTEMPTS}] transient empty or failed fetch"
    stderr = (result.get("stderr") or "").strip()
    result["stderr"] = f"{stderr}\n{note}".strip()


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


def fetch_section_with_retry(section: dict, limit_override: int | None = None) -> dict:
    result = fetch_section(section, limit_override)
    for attempt in range(2, RETRY_ATTEMPTS + 1):
        if not should_retry(section, result):
            break
        annotate_retry(result, attempt - 1)
        time.sleep(RETRY_DELAY_SECONDS)
        result = fetch_section(section, limit_override)
    return result



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

    results = [fetch_section_with_retry(section, args.limit_override) for section in sections]
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
