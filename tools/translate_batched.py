#!/usr/bin/env python3
"""Batch translation via OpenRouter API. Splits items into small batches to stay within output token limits."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from common import read_json, report_dir, today_str, write_json

BATCH_SIZE = 50
MODEL = "gemini-3.1-flash-lite"
GOOGLE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def call_google(items: list[dict], api_key: str) -> list[dict]:
    prompt = (
        "Translate each item to Russian. Return ONLY a valid JSON array, no explanations.\n"
        "Rules:\n"
        "- id: keep unchanged\n"
        "- title_ru: natural Russian translation of title_original\n"
        "- description_ru: exactly one short neutral Russian sentence\n"
        "- Translate from English, Chinese, or any non-Russian language\n\n"
        f"Input:\n{json.dumps(items, ensure_ascii=False)}\n\n"
        'Output format: [{"id":"...","title_ru":"...","description_ru":"..."}]'
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }).encode()

    req = urllib.request.Request(
        f"{GOOGLE_API_URL}?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    content = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    start = content.find("[")
    end = content.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array in response: {content[:300]}")

    return json.loads(content[start:end])


def translate_all(all_items: list[dict], api_key: str) -> list[dict]:
    results = []
    total_batches = (len(all_items) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(all_items), BATCH_SIZE):
        batch = all_items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Batch {batch_num}/{total_batches} ({len(batch)} items)...", end=" ", flush=True)

        for attempt in range(3):
            try:
                result = call_google(batch, api_key)
                results.extend(result)
                print(f"OK ({len(result)} translated)", flush=True)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"FAILED after 3 attempts: {e}", flush=True)
                    sys.exit(1)
                print(f"retry {attempt + 1}... ", end="", flush=True)
                time.sleep(5)

        # Pause between batches to stay under 250K TPM/min limit
        if i + BATCH_SIZE < len(all_items):
            time.sleep(15)

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("ERROR: GOOGLE_API_KEY not set in environment")

    day_dir = report_dir(args.date)
    ai_input_path = day_dir / "ai_input.json"
    ai_output_path = day_dir / "ai_output.json"

    if not ai_input_path.exists():
        sys.exit(f"ERROR: {ai_input_path} not found — run build_report.py --mode prepare-ai first")

    data = read_json(ai_input_path)

    all_items = [
        {
            "id": item["id"],
            "title_original": item.get("title_original", ""),
            "snippet": item.get("snippet", ""),
        }
        for section in data.get("sections", [])
        for item in section.get("items", [])
    ]

    print(f"Translating {len(all_items)} items in batches of {BATCH_SIZE} using {MODEL}", flush=True)

    translated = translate_all(all_items, api_key)

    write_json(ai_output_path, {
        "provider": "openclaw-agent",
        "items": translated,
    })
    print(f"Done: {len(translated)} items written to {ai_output_path}", flush=True)


if __name__ == "__main__":
    main()
