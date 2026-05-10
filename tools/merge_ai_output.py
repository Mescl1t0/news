#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import derive_description, read_json, report_dir, safe_text, today_str, write_json


def merge(normalized: dict, ai_output: dict) -> dict:
    ai_items = {item["id"]: item for item in ai_output.get("items", []) if item.get("id")}
    missing = []
    for section in normalized.get("sections", []):
        for item in section.get("items", []):
            ai_item = ai_items.get(item["id"])
            if ai_item:
                item["title_ru"] = safe_text(ai_item.get("title_ru")) or item.get("title_ru") or item.get("title_original")
                item["description_ru"] = safe_text(ai_item.get("description_ru")) or item.get("description_ru") or derive_description(item)
            else:
                missing.append(item["id"])
                item["title_ru"] = safe_text(item.get("title_ru") or item.get("title_original"))
                item["description_ru"] = safe_text(item.get("description_ru")) or derive_description(item)
    normalized["enrichment"] = {
        "used_llm": bool(ai_items),
        "provider": ai_output.get("provider", "openclaw-agent" if ai_items else "fallback"),
        "mode": "compact-ai-input",
        "missing_ai_items": missing,
    }
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--normalized", default=None)
    parser.add_argument("--ai-output", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    normalized_path = Path(args.normalized) if args.normalized else day_dir / "normalized.json"
    ai_output_path = Path(args.ai_output) if args.ai_output else day_dir / "ai_output.json"
    out_path = Path(args.out) if args.out else day_dir / "enriched.json"
    write_json(out_path, merge(read_json(normalized_path), read_json(ai_output_path)))
    print(out_path)


if __name__ == "__main__":
    main()
