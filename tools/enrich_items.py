#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from common import derive_description, maybe_translate_title, read_json, report_dir, safe_text, today_str, write_json

PROMPT = (
    "Ты редактор русскоязычного новостного дайджеста. "
    "Для каждого элемента верни JSON с полями title_ru и description_ru. "
    "title_ru: естественный русский заголовок без кликбейта. "
    "description_ru: ровно одно нейтральное предложение на русском без оценки."
)


def llm_enrich(title: str, description: str) -> dict | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("NEWS_ENRICH_MODEL", os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": json.dumps({"title": title, "description": description}, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            response = json.loads(resp.read().decode("utf-8"))
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        title_ru = safe_text(parsed.get("title_ru"))
        desc_ru = safe_text(parsed.get("description_ru"))
        if title_ru or desc_ru:
            return {"title_ru": title_ru or title, "description_ru": desc_ru or description}
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None
    return None



def enrich_payload(payload: dict) -> dict:
    used_llm = False
    for section in payload.get("sections", []):
        for item in section.get("items", []):
            original_title = safe_text(item.get("title_original") or item.get("title_ru"))
            fallback_desc = safe_text(item.get("description_ru")) or derive_description(item.get("raw", {}))
            enriched = llm_enrich(original_title, fallback_desc)
            if enriched:
                used_llm = True
                item["title_ru"] = enriched["title_ru"]
                item["description_ru"] = enriched["description_ru"]
            else:
                item["title_ru"] = safe_text(item.get("title_ru")) or maybe_translate_title(original_title)
                item["description_ru"] = fallback_desc
    payload["enrichment"] = {
        "used_llm": used_llm,
        "provider": "openai-compatible" if used_llm else "fallback",
    }
    return payload



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--normalized", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    normalized_path = Path(args.normalized) if args.normalized else day_dir / "normalized.json"
    out_path = Path(args.out) if args.out else day_dir / "enriched.json"

    enriched = enrich_payload(read_json(normalized_path))
    write_json(out_path, enriched)
    print(out_path)


if __name__ == "__main__":
    main()
