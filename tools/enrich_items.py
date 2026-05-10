#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import derive_description, maybe_translate_title, read_json, report_dir, safe_text, today_str, write_json


def fallback_enrich_payload(payload: dict) -> dict:
    """
    Deterministic fallback enrichment.

    This script intentionally does NOT call an external LLM API. In this project,
    real AI enrichment is done by the OpenClaw agent between normalize and render:

      1. tools/build_report.py --mode prepare-ai --date YYYY-MM-DD
      2. OpenClaw agent reads normalized.json and writes enriched.json
      3. tools/build_report.py --mode publish-ai --date YYYY-MM-DD

    The fallback exists only so the renderer can still work when AI enrichment is
    intentionally skipped.
    """
    for section in payload.get("sections", []):
        for item in section.get("items", []):
            original_title = safe_text(item.get("title_original") or item.get("title_ru"))
            item["title_ru"] = safe_text(item.get("title_ru")) or maybe_translate_title(original_title)
            item["description_ru"] = safe_text(item.get("description_ru")) or derive_description(item)
    payload["enrichment"] = {
        "used_llm": False,
        "provider": "openclaw-agent-required",
        "mode": "deterministic-fallback",
        "note": "Real AI translation/summary must be produced by OpenClaw agent from normalized.json.",
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fallback-only enrichment; no external API calls.")
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--normalized", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    normalized_path = Path(args.normalized) if args.normalized else day_dir / "normalized.json"
    out_path = Path(args.out) if args.out else day_dir / "enriched.json"

    enriched = fallback_enrich_payload(read_json(normalized_path))
    write_json(out_path, enriched)
    print(out_path)


if __name__ == "__main__":
    main()
