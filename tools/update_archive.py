#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from common import PUBLIC_DIR, REPORTS_DIR

CSS = ":root{color-scheme:light;--bg:#f8fafc;--panel:#fff;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#2563eb;--hover:#f8fbff;--shadow:0 8px 30px rgba(15,23,42,.06)}*{box-sizing:border-box}body{margin:0;font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:var(--bg);color:var(--text)}main{max-width:1080px;margin:0 auto;padding:32px 18px 64px}.hero,.card{background:var(--panel);border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow)}.hero{padding:28px;margin-bottom:18px}.card{padding:22px}h1{margin:0 0 8px;font-size:clamp(30px,5vw,48px);line-height:1.05}h2{margin:0 0 14px;font-size:1.25rem}.meta{color:var(--muted)}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}ul{margin:0;padding-left:1.2rem}.summary li{margin:.55rem 0}.file-links{display:inline-flex;gap:10px;flex-wrap:wrap}.tag{display:inline-flex;padding:2px 8px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:.78rem;margin-left:6px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.btn{display:inline-flex;padding:10px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel);text-decoration:none}.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}@media (max-width:640px){main{padding:22px 14px 44px}}"


def cleanup_and_list_days(reports_dir: Path, latest_day: str, keep_days: int = 30) -> list[str]:
    days = []
    if not reports_dir.exists():
        return days
    latest = datetime.strptime(latest_day, "%Y-%m-%d").date()
    cutoff = latest - timedelta(days=keep_days - 1)
    for child in reports_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            child_day = datetime.strptime(child.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if child_day < cutoff:
            shutil.rmtree(child)
            continue
        if (child / "index.html").exists():
            days.append(child.name)
    return sorted(days, reverse=True)


def write_latest_index(latest_day: str, out_path: Path) -> None:
    esc = html.escape(latest_day)
    page = f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=reports/{esc}/"><title>Последний новостной выпуск</title><style>{CSS}</style></head><body><main><section class="hero"><h1>Последний новостной выпуск</h1><div class="meta">Открываем последний выпуск: {esc}</div><div class="actions"><a class="btn primary" href="reports/{esc}/">Открыть выпуск</a><a class="btn" href="archive.html">Архив</a></div></section></main></body></html>'
    out_path.write_text(page, encoding="utf-8")


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
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Архив новостных выпусков</title><style>{CSS}</style></head><body><main><section class="hero"><h1>Архив новостных выпусков</h1><div class="meta">Последние 30 статических HTML-выпусков.</div><div class="actions"><a class="btn primary" href="reports/{html.escape(latest_day)}/">Последний выпуск</a></div></section><section class="card"><h2>Выпуски</h2><ul class="summary">{list_html}</ul></section></main></body></html>'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest-date", required=True)
    parser.add_argument("--out", default=str(PUBLIC_DIR / "index.html"))
    parser.add_argument("--archive-out", default=str(PUBLIC_DIR / "archive.html"))
    parser.add_argument("--keep-days", type=int, default=30)
    args = parser.parse_args()

    days = cleanup_and_list_days(REPORTS_DIR, args.latest_date, args.keep_days)
    Path(args.out).write_text("", encoding="utf-8")
    write_latest_index(args.latest_date, Path(args.out))
    Path(args.archive_out).write_text(build_archive_index(days, args.latest_date), encoding="utf-8")
    print(args.out)
    print(args.archive_out)


if __name__ == "__main__":
    main()
