#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import derive_description, load_sections, read_json, report_dir, safe_text, today_str, write_json


def normalize_source_items(section: dict, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for index, item in enumerate(raw_items, start=1):
        url = safe_text(item.get("url"))
        title = safe_text(item.get("title"))
        if not title or not url:
            continue
        items.append({
            "id": f"{section['id']}-{index}",
            "section_id": section["id"],
            "position": index,
            "source": safe_text(item.get("source") or section["title"]),
            "title_original": title,
            "title_ru": safe_text(item.get("title_ru")) or title,
            "description_ru": safe_text(item.get("description_ru")) or derive_description(item),
            "url": url,
            "metadata": {
                "time": safe_text(item.get("time")),
                "heat": safe_text(item.get("heat")),
                "hn_url": safe_text(item.get("hn_url")),
                "discussion_url": safe_text(item.get("discussion_url")),
            },
        })
    return items



def normalize_digest_items(section: dict, raw_sections: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    items = []
    position = 1
    for subsection_name, subsection_items in raw_sections.items():
        for item in subsection_items or []:
            url = safe_text(item.get("url"))
            title = safe_text(item.get("title"))
            if not title or not url:
                continue
            items.append({
                "id": f"{section['id']}-{position}",
                "section_id": section["id"],
                "position": position,
                "subsection": subsection_name,
                "source": safe_text(item.get("source") or section["title"]),
                "title_original": title,
                "title_ru": safe_text(item.get("title_ru")) or title,
                "description_ru": safe_text(item.get("description_ru")) or derive_description(item),
                "url": url,
                "metadata": {
                    "time": safe_text(item.get("time")),
                    "heat": safe_text(item.get("heat")),
                },
            })
            position += 1
    return items



def normalize(raw_payload: dict, config_sections: list[dict], max_items_per_section: int | None = None) -> dict:
    section_map = {section["id"]: section for section in config_sections}
    normalized_sections = []
    for entry in raw_payload.get("sections", []):
        config = section_map.get(entry["id"])
        if not config:
            continue
        raw = entry.get("raw")
        items = normalize_digest_items(config, raw) if config["type"] == "digest" else normalize_source_items(config, raw)
        limit = max_items_per_section or config.get("default_limit")
        if limit:
            items = items[:int(limit)]
        normalized_sections.append({
            "id": config["id"],
            "title": config["title"],
            "type": config["type"],
            "order": config["order"],
            "sidebar_group": config.get("sidebar_group", "Источники"),
            "description": config.get("description", ""),
            "default_limit": config.get("default_limit"),
            "allow_empty": bool(config.get("allow_empty", False)),
            "returncode": entry.get("returncode", 0),
            "stderr": entry.get("stderr", ""),
            "count": len(items),
            "items": items,
        })
    normalized_sections.sort(key=lambda item: int(item["order"]))
    return {
        "date": raw_payload["date"],
        "generated_at": raw_payload.get("generated_at"),
        "sections": normalized_sections,
    }



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--raw", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-items-per-section", type=int, default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    raw_path = Path(args.raw) if args.raw else day_dir / "raw.json"
    out_path = Path(args.out) if args.out else day_dir / "normalized.json"
    config_path = Path(args.config) if args.config else Path(__file__).resolve().parent.parent / "config" / "sections.json"

    normalized = normalize(read_json(raw_path), load_sections(config_path), args.max_items_per_section)
    write_json(out_path, normalized)
    print(out_path)


if __name__ == "__main__":
    main()
