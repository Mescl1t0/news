#!/usr/bin/env python3
"""Batch translation via Google Gemini API.

Splits items into small batches for free-tier reliability and post-validates the
model output before writing ai_output.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from common import has_cyrillic, read_json, report_dir, safe_text, today_str, write_json

BATCH_SIZE = int(os.environ.get("NEWS_TRANSLATE_BATCH_SIZE", "25"))
BATCH_PAUSE_SECONDS = int(os.environ.get("NEWS_TRANSLATE_BATCH_PAUSE_SECONDS", "20"))
MAX_ATTEMPTS = int(os.environ.get("NEWS_TRANSLATE_MAX_ATTEMPTS", "5"))
MODEL = "gemini-3.1-flash-lite"
GOOGLE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def call_google(items: list[dict], api_key: str) -> list[dict]:
    prompt = (
        "Translate each item to Russian. Return ONLY a valid JSON array, no explanations.\n"
        "Rules:\n"
        "- id: keep unchanged\n"
        "- title_ru: natural Russian headline translated from title_original\n"
        "- title_ru MUST contain Cyrillic text unless title_original already contains Cyrillic\n"
        "- Preserve product/repo names, but if a title is only a name, add a short Russian explanation after an em dash\n"
        "  Example: GenCAD -> GenCAD — система автоматизированного проектирования\n"
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


def retry_delay_seconds(attempt: int, error: Exception) -> int:
    if isinstance(error, urllib.error.HTTPError):
        retry_after = error.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(int(retry_after), 90)
    return min(5 * (2 ** attempt), 90)


def validate_batch_result(batch: list[dict], result: list[dict]) -> None:
    if not isinstance(result, list):
        raise ValueError("Model response is not a JSON array")
    expected = [safe_text(item.get("id")) for item in batch]
    actual = [safe_text(item.get("id")) for item in result]
    if len(actual) != len(expected):
        raise ValueError(f"Expected {len(expected)} translations, got {len(actual)}")
    missing = [item_id for item_id in expected if item_id not in actual]
    duplicate = sorted({item_id for item_id in actual if actual.count(item_id) > 1})
    if missing or duplicate:
        raise ValueError(f"Bad translation ids: missing={missing[:5]}, duplicate={duplicate[:5]}")


def title_suffix_from_description(description_ru: str) -> str:
    text = re.sub(r"\s+", " ", safe_text(description_ru)).strip(" .")
    if not has_cyrillic(text):
        return "краткий обзор"
    return text[:1].lower() + text[1:120]


def repair_title(original: str, translated: str, description_ru: str) -> str:
    original = safe_text(original)
    translated = safe_text(translated) or original
    if not original or has_cyrillic(original):
        return translated
    title_base = safe_text(translated.split(" — ", 1)[0]) or original
    if has_cyrillic(translated) and has_cyrillic(title_base):
        return translated
    return f"{title_base} — {title_suffix_from_description(description_ru)}"


def repair_translations(all_items: list[dict], translated: list[dict]) -> list[dict]:
    by_id = {safe_text(item.get("id")): item for item in translated}
    repaired: list[dict] = []
    for source_item in all_items:
        item_id = safe_text(source_item.get("id"))
        item = dict(by_id.get(item_id) or {"id": item_id})
        description_ru = safe_text(item.get("description_ru"))
        if not has_cyrillic(description_ru):
            description_ru = "Материал требует краткого русскоязычного описания."
        repaired.append({
            "id": item_id,
            "title_ru": repair_title(
                safe_text(source_item.get("title_original")),
                safe_text(item.get("title_ru")),
                description_ru,
            ),
            "description_ru": description_ru,
        })
    return repaired


def translate_all(all_items: list[dict], api_key: str) -> list[dict]:
    results = []
    total_batches = (len(all_items) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(all_items), BATCH_SIZE):
        batch = all_items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Batch {batch_num}/{total_batches} ({len(batch)} items)...", end=" ", flush=True)

        for attempt in range(MAX_ATTEMPTS):
            try:
                result = call_google(batch, api_key)
                validate_batch_result(batch, result)
                results.extend(result)
                print(f"OK ({len(result)} translated)", flush=True)
                break
            except Exception as e:
                if attempt == MAX_ATTEMPTS - 1:
                    print(f"FAILED after {MAX_ATTEMPTS} attempts: {e}", flush=True)
                    sys.exit(1)
                delay = retry_delay_seconds(attempt, e)
                print(f"retry {attempt + 1} in {delay}s... ", end="", flush=True)
                time.sleep(delay)

        # Pause between batches to stay friendlier to free-tier RPM/TPM limits.
        if i + BATCH_SIZE < len(all_items):
            time.sleep(BATCH_PAUSE_SECONDS)

    return repair_translations(all_items, results)


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
