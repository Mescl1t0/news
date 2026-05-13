#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, report_dir, safe_text, today_str, write_json


def compact_item(item: dict) -> dict:
    snippet = safe_text(item.get("description_ru"))
    if len(snippet) > 260:
        snippet = snippet[:257].rstrip() + "…"
    return {
        "id": item["id"],
        "section_id": item["section_id"],
        "title_original": safe_text(item.get("title_original") or item.get("title_ru")),
        "snippet": snippet,
    }


def build_ai_input(normalized: dict) -> dict:
    sections = []
    for section in normalized.get("sections", []):
        items = [compact_item(item) for item in section.get("items", [])]
        sections.append({
            "id": section["id"],
            "title": section["title"],
            "items": items,
        })
    return {
        "date": normalized["date"],
        "task": (
            "For every item keep title_original unchanged, add a natural Russian translation into title_ru, "
            "and write exactly one short neutral Russian sentence into description_ru. "
            "Do not leave English-only or placeholder text in title_ru/description_ru. Return ai_output schema only."
        ),
        "output_schema": {
            "items": [
                {
                    "id": "same id from input",
                    "title_original": "same original title from input",
                    "title_ru": "natural Russian headline",
                    "description_ru": "exactly one neutral Russian sentence",
                }
            ]
        },
        "sections": sections,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--normalized", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    normalized_path = Path(args.normalized) if args.normalized else day_dir / "normalized.json"
    out_path = Path(args.out) if args.out else day_dir / "ai_input.json"
    write_json(out_path, build_ai_input(read_json(normalized_path)))
    print(out_path)


if __name__ == "__main__":
    main()
