#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from datetime import datetime
from pathlib import Path

from common import PUBLIC_DIR, REPORTS_DIR

CSS = ":root{color-scheme:light;--bg:#f8fafc;--panel:#fff;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#2563eb;--hover:#f8fbff;--shadow:0 8px 30px rgba(15,23,42,.06)}*{box-sizing:border-box}body{margin:0;font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:var(--bg);color:var(--text)}main{max-width:1080px;margin:0 auto;padding:32px 18px 64px}.hero,.card{background:var(--panel);border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow)}.hero{padding:28px;margin-bottom:18px}.card{padding:22px}h1{margin:0 0 8px;font-size:clamp(30px,5vw,48px);line-height:1.05}h2{margin:0 0 14px;font-size:1.25rem}.meta{color:var(--muted)}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}ul{margin:0;padding-left:1.2rem}.summary li{margin:.55rem 0}.file-links{display:inline-flex;gap:10px;flex-wrap:wrap}.tag{display:inline-flex;padding:2px 8px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:.78rem;margin-left:6px}@media (max-width:640px){main{padding:22px 14px 44px}}"


def available_days(reports_dir: Path) -> list[str]:
    days = []
    if not reports_dir.exists():
        return days
    for child in reports_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            datetime.strptime(child.name, "%Y-%m-%d")
        except ValueError:
            continue
        if (child / "index.html").exists():
            days.append(child.name)
    return sorted(days, reverse=True)



def build_archive_index(days: list[str], latest_day: str) -> str:
    items = []
    for day in days:
        esc = html.escape(day)
        label = '<span class="tag">последний</span>' if day == latest_day else ''
        links = [f'<a href="reports/{esc}/">HTML</a>']
        for filename, title in [("raw.json", "Raw"), ("normalized.json", "Normalized"), ("enriched.json", "Enriched")]:
            if (REPORTS_DIR / day / filename).exists():
                links.append(f'<a href="reports/{esc}/{filename}">{title}</a>')
        items.append(f'<li><a href="reports/{esc}/">{esc}</a>{label} · <span class="file-links">{" · ".join(links)}</span></li>')
    list_html = "\n".join(items) if items else "<li>Пока нет отчётов.</li>"
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Архив новостных выпусков</title><style>{CSS}</style></head><body><main><section class="hero"><h1>Архив новостных выпусков</h1><div class="meta">Статические HTML-выпуски с raw / normalized / enriched данными.</div></section><section class="card"><h2>Выпуски</h2><ul class="summary">{list_html}</ul></section></main></body></html>'



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest-date", required=True)
    parser.add_argument("--out", default=str(PUBLIC_DIR / "index.html"))
    args = parser.parse_args()

    days = available_days(REPORTS_DIR)
    out_path = Path(args.out)
    out_path.write_text(build_archive_index(days, args.latest_date), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
