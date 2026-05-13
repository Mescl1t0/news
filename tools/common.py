#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT / "public"
REPORTS_DIR = PUBLIC_DIR / "reports"
CONFIG_PATH = ROOT / "config" / "sections.json"
SKILL_ROOT = Path("/home/node/.openclaw/workspace/skills/news-aggregator-skill")
SKILL_SCRIPTS = SKILL_ROOT / "scripts"
FETCH_SCRIPT = SKILL_SCRIPTS / "fetch_news.py"
BRIEFING_SCRIPT = SKILL_SCRIPTS / "daily_briefing.py"


@dataclass
class SectionConfig:
    raw: dict[str, Any]

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def title(self) -> str:
        return self.raw["title"]

    @property
    def order(self) -> int:
        return int(self.raw["order"])

    @property
    def visible(self) -> bool:
        return bool(self.raw.get("visible", True))

    @property
    def sidebar_group(self) -> str:
        return self.raw.get("sidebar_group", "Источники")

    @property
    def default_limit(self) -> int | None:
        value = self.raw.get("default_limit")
        return None if value is None else int(value)



def load_sections(config_path: Path = CONFIG_PATH) -> list[dict[str, Any]]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    sections = [item for item in data if item.get("visible", True)]
    return sorted(sections, key=lambda item: int(item["order"]))



def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path



def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))



def write_json(path: Path, data: Any) -> Path:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path



def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9а-яё]+", "-", value, flags=re.I)
    return value.strip("-") or "section"



def report_dir(day: str) -> Path:
    return REPORTS_DIR / day



def today_str() -> str:
    return date.today().isoformat()



def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")



def run_json_command(command: list[str], cwd: Path) -> tuple[Any, str, int]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SKILL_ROOT}:{SKILL_SCRIPTS}:{existing}" if existing else f"{SKILL_ROOT}:{SKILL_SCRIPTS}"
    proc = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True)
    stdout = proc.stdout.strip()
    parsed = None
    if stdout:
        parsed = json.loads(stdout)
    return parsed, proc.stderr, proc.returncode



def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def has_cyrillic(value: Any) -> bool:
    return bool(re.search(r"[А-Яа-яЁёІіЇїЄє]", safe_text(value)))


def has_latin(value: Any) -> bool:
    return bool(re.search(r"[A-Za-z]", safe_text(value)))


def is_placeholder_description(value: Any) -> bool:
    text = safe_text(value)
    if not text:
        return True
    placeholder_prefixes = (
        "Материал посвящён теме",
        "Материал посвящен теме",
    )
    return text.startswith(placeholder_prefixes)


def needs_russian_title(title_original: Any, title_ru: Any) -> bool:
    original = safe_text(title_original)
    translated = safe_text(title_ru)
    if not original:
        return False
    if has_cyrillic(translated):
        return False
    if not translated:
        return True
    return not has_cyrillic(original)



def derive_description(item: dict[str, Any]) -> str:
    candidates = [
        item.get("description_ru"),
        item.get("summary_ru"),
        item.get("summary"),
        item.get("deep_dive"),
        item.get("content_summary"),
        item.get("content"),
        item.get("description"),
    ]
    for candidate in candidates:
        text = safe_text(candidate)
        if text:
            text = re.sub(r"\s+", " ", text)
            text = text.replace("Коротко:", "").strip(" -–—")
            sentences = re.split(r"(?<=[.!?])\s+", text)
            best = sentences[0].strip() if sentences else text
            if best and not re.search(r"[.!?…]$", best):
                best += "."
            return best[:280]
    title = safe_text(item.get("title_ru") or item.get("title_original") or item.get("title"))
    if not title:
        return ""
    return f"Материал посвящён теме «{title}»."



def maybe_translate_title(title: str) -> str:
    return safe_text(title)



def render_count_label(count: int) -> str:
    return f"{count} материал{'ов' if count % 10 == 0 or count % 10 >= 5 or 10 < count % 100 < 20 else 'а' if count % 10 in (2,3,4) and not 10 < count % 100 < 20 else ''}"
