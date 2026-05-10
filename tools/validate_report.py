#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import load_sections, read_json, report_dir, today_str


def validate(payload: dict, config_sections: list[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config_map = {section["id"]: section for section in config_sections}
    seen = set()
    for section in payload.get("sections", []):
        sid = section["id"]
        seen.add(sid)
        cfg = config_map.get(sid)
        if not cfg:
            errors.append(f"Unknown section in payload: {sid}")
            continue
        items = section.get("items", [])
        count = section.get("count")
        if count != len(items):
            errors.append(f"Count mismatch for {sid}: count={count}, items={len(items)}")
        if not items:
            if cfg.get("allow_empty", False):
                warnings.append(f"Section {sid} is empty but allowed")
            else:
                errors.append(f"Section {sid} has no items")
        for item in items:
            if not item.get("url"):
                errors.append(f"Item without url in section {sid}: {item.get('id')}")
            if not item.get("title_ru") and not item.get("title_original"):
                errors.append(f"Item without title in section {sid}: {item.get('id')}")
            if not item.get("description_ru"):
                warnings.append(f"Item without description in section {sid}: {item.get('id')}")
    missing = [section["id"] for section in config_sections if section["id"] not in seen]
    if missing:
        errors.append("Missing sections: " + ", ".join(missing))
    return errors, warnings



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--in", dest="input_path", default=None)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    input_path = Path(args.input_path) if args.input_path else day_dir / "enriched.json"
    config_path = Path(args.config) if args.config else Path(__file__).resolve().parent.parent / "config" / "sections.json"

    errors, warnings = validate(read_json(input_path), load_sections(config_path))
    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
