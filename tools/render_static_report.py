#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from pathlib import Path

from common import read_json, report_dir, safe_text, today_str

CSS = """
:root{color-scheme:light;--bg:#f8fafc;--panel:#ffffff;--panel-2:#f8fafc;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;--line-2:#f1f5f9;--accent:#2563eb;--accent-soft:#dbeafe;--hover:#f8fbff;--shadow:0 8px 30px rgba(15,23,42,.06)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:var(--bg);color:var(--text)}button,input,select,textarea{font:inherit}a{color:inherit}header{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}.header-inner{max-width:1440px;margin:0 auto;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{display:flex;align-items:center;gap:12px;min-width:0}.brand-mark{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#3b82f6,#1d4ed8);display:flex;align-items:center;justify-content:center;color:#fff;font-size:18px;font-weight:700;flex:0 0 auto}.brand-copy{min-width:0}.brand-copy h1{margin:0;font-size:1.05rem;font-weight:650;line-height:1.2}.brand-copy p{margin:2px 0 0;color:var(--muted);font-size:.84rem}.archive-link{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel);text-decoration:none;color:var(--muted);white-space:nowrap}.archive-link:hover{background:var(--hover);color:var(--text)}.layout{max-width:1440px;margin:0 auto;display:grid;grid-template-columns:280px minmax(0,1fr);min-height:calc(100vh - 73px)}.sidebar{position:sticky;top:73px;height:calc(100vh - 73px);overflow:auto;background:var(--panel);border-right:1px solid var(--line)}.sidebar-inner{padding:22px 16px 28px}.side-group+.side-group{margin-top:24px}.side-label{display:flex;align-items:center;gap:8px;margin:0 0 10px;padding:0 8px;color:var(--muted);font-size:.73rem;letter-spacing:.08em;text-transform:uppercase}.nav-list{display:grid;gap:4px}.nav-btn{width:100%;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border:0;background:transparent;border-radius:12px;color:#334155;text-align:left;cursor:pointer}.nav-btn:hover{background:#f8fafc}.nav-btn.is-active{background:var(--accent-soft);color:var(--accent)}.nav-title{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.nav-count{padding:3px 8px;border-radius:999px;background:#f1f5f9;color:var(--muted);font-size:.78rem;flex:0 0 auto}.nav-btn.is-active .nav-count{background:#bfdbfe;color:var(--accent)}.content{padding:24px 28px 48px}.page-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 18px}.page-meta h2{margin:0;font-size:1.25rem;font-weight:650}.page-meta p{margin:0;color:var(--muted);font-size:.92rem}.meta-links{display:flex;gap:10px;flex-wrap:wrap}.meta-links a{display:inline-flex;padding:8px 12px;border-radius:999px;border:1px solid var(--line);text-decoration:none;color:var(--muted)}.meta-links a:hover{background:var(--hover);color:var(--text)}.mobile-tabs{display:none;gap:10px;overflow:auto;padding:2px 0 2px 2px;margin:0 0 18px;scrollbar-width:none}.mobile-tabs::-webkit-scrollbar{display:none}.mobile-tab{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:#334155;white-space:nowrap;cursor:pointer}.mobile-tab.is-active{background:var(--accent-soft);border-color:#bfdbfe;color:var(--accent)}.mobile-count{padding:2px 7px;border-radius:999px;background:#f1f5f9;color:var(--muted);font-size:.76rem}.mobile-tab.is-active .mobile-count{background:#bfdbfe;color:var(--accent)}.section-card{background:var(--panel);border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:var(--shadow)}.section-head{padding:22px 24px;border-bottom:1px solid var(--line)}.section-head h3{margin:0;font-size:1.6rem;line-height:1.15;font-weight:650}.section-head p{margin:6px 0 0;color:var(--muted);font-size:.95rem}.news-list{display:grid}.news-item{display:block;padding:18px 24px;text-decoration:none;border-bottom:1px solid var(--line-2);transition:background-color .15s ease}.news-item:last-child{border-bottom:0}.news-item:hover{background:var(--hover)}.news-title{display:block;font-size:1.02rem;line-height:1.38;font-weight:520;color:var(--text)}.news-desc{display:block;margin-top:6px;font-size:.95rem;line-height:1.55;color:var(--muted)}.section-panel[hidden]{display:none!important}.empty-note{padding:18px 24px;color:var(--muted)}.footer-note{margin-top:14px;color:var(--muted);font-size:.88rem}@media (max-width:1100px){.layout{grid-template-columns:1fr}.sidebar{display:none}.content{padding:18px 16px 40px}.mobile-tabs{display:flex}.section-head,.news-item,.empty-note{padding-left:18px;padding-right:18px}}@media (max-width:640px){.header-inner{padding:14px 14px}.archive-link span{display:none}.brand-copy h1{font-size:1rem}.section-head h3{font-size:1.28rem}.news-title{font-size:.98rem}.news-desc{font-size:.92rem}}
"""


def e(value: str) -> str:
    return html.escape(value, quote=True)


def render_nav_buttons(sections: list[dict], mobile: bool = False) -> str:
    class_name = "mobile-tab" if mobile else "nav-btn"
    count_class = "mobile-count" if mobile else "nav-count"
    parts = []
    for index, section in enumerate(sections):
        active = " is-active" if index == 0 else ""
        pressed = "true" if index == 0 else "false"
        parts.append(
            f'<button class="{class_name}{active}" type="button" data-section-target="{e(section["id"])}" aria-pressed="{pressed}">'
            f'<span class="nav-title">{e(section["title"])}</span>'
            f'<span class="{count_class}">{section["count"]}</span>'
            f'</button>'
        )
    return "".join(parts)



def render_sidebar_groups(sections: list[dict]) -> str:
    groups: dict[str, list[dict]] = {}
    for section in sections:
        groups.setdefault(section.get("sidebar_group", "Источники"), []).append(section)
    chunks = []
    for group_name, group_sections in groups.items():
        chunks.append(f'<div class="side-group"><h2 class="side-label">{e(group_name)}</h2><div class="nav-list">{render_nav_buttons(group_sections)}</div></div>')
    return "".join(chunks)



def render_section(section: dict, active: bool) -> str:
    hidden = "" if active else " hidden"
    if section["items"]:
        items_html = "".join(
            f'<a class="news-item" href="{e(item["url"])}" target="_blank" rel="noopener">'
            f'<span class="news-title">{e(item.get("title_ru") or item.get("title_original") or "Без названия")}</span>'
            f'<span class="news-desc">{e(item.get("description_ru") or "")}</span>'
            f'</a>'
            for item in section["items"]
        )
    else:
        items_html = '<div class="empty-note">Для этого раздела пока нет материалов.</div>'
    description = section.get("description") or ""
    count_text = f'{section["count"]} материалов' if section["count"] != 1 else '1 материал'
    if description:
        description = f'{count_text} · {description}'
    else:
        description = count_text
    return (
        f'<section class="section-panel" data-section="{e(section["id"])}"{hidden}>'
        f'<div class="section-card"><div class="section-head"><h3>{e(section["title"])}</h3>'
        f'<p>{e(description)}</p></div><div class="news-list">{items_html}</div></div></section>'
    )



def build_html(payload: dict) -> str:
    sections = payload["sections"]
    first_title = sections[0]["title"] if sections else "Выпуск"
    sidebar = render_sidebar_groups(sections)
    mobile_tabs = render_nav_buttons(sections, mobile=True)
    section_panels = "".join(render_section(section, index == 0) for index, section in enumerate(sections))
    date_text = e(payload["date"])
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Новостной выпуск · {date_text}</title><style>{CSS}</style></head><body><header><div class="header-inner"><div class="brand"><div class="brand-mark">N</div><div class="brand-copy"><h1>Новостной выпуск</h1><p>{date_text} · статический отчёт</p></div></div><a class="archive-link" href="../../archive.html"><span>←</span> Архив</a></div></header><div class="layout"><aside class="sidebar"><div class="sidebar-inner">{sidebar}</div></aside><main class="content"><div class="page-meta"><div><h2>{e(first_title)}</h2><p>Разделы переключаются без перезагрузки страницы; данные собраны и отрендерены скриптами.</p></div><div class="meta-links"><a href="./raw.json">Raw</a><a href="./normalized.json">Normalized</a><a href="./enriched.json">Enriched</a></div></div><div class="mobile-tabs" aria-label="Разделы выпуска">{mobile_tabs}</div>{section_panels}<p class="footer-note">Автогенерируемый выпуск без markdown-слоя: fetch → normalize → enrich → render.</p></main></div><script>(()=>{{const buttons=[...document.querySelectorAll('[data-section-target]')];const panels=[...document.querySelectorAll('.section-panel')];function activate(target){{panels.forEach(panel=>{{panel.hidden=panel.dataset.section!==target;}});buttons.forEach(btn=>{{const active=btn.dataset.sectionTarget===target;btn.classList.toggle('is-active',active);btn.setAttribute('aria-pressed',String(active));}});}}buttons.forEach(btn=>btn.addEventListener('click',()=>activate(btn.dataset.sectionTarget)));if(buttons[0])activate(buttons[0].dataset.sectionTarget);}})();</script></body></html>'''



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=today_str())
    parser.add_argument("--in", dest="input_path", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    day_dir = report_dir(args.date)
    input_path = Path(args.input_path) if args.input_path else day_dir / "enriched.json"
    out_path = Path(args.out) if args.out else day_dir / "index.html"
    payload = read_json(input_path)
    out_path.write_text(build_html(payload), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
