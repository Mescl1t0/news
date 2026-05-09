#!/usr/bin/env python3
import argparse, html, json, re, shutil
from datetime import date, datetime, timedelta
from pathlib import Path

CSS = """
:root{color-scheme:light dark;--bg:#0b1020;--card:#121a2f;--text:#e8eefc;--muted:#98a4bd;--line:#26324d;--accent:#7dd3fc;--ok:#86efac;--warn:#fde68a;--bad:#fca5a5}*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:linear-gradient(135deg,#08111f,#111827 50%,#0f172a);color:var(--text)}main{max-width:1180px;margin:auto;padding:32px 18px 64px}.hero{border:1px solid var(--line);background:rgba(18,26,47,.86);border-radius:22px;padding:28px;box-shadow:0 16px 60px rgba(0,0,0,.25)}h1{margin:0 0 10px;font-size:clamp(28px,5vw,48px);line-height:1.05}.meta{color:var(--muted)}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:22px 0}.card,details{border:1px solid var(--line);background:rgba(18,26,47,.78);border-radius:18px;padding:18px}.card h3{margin:.1rem 0 .6rem}.summary li{margin:.38rem 0}details{margin:14px 0;padding:0;overflow:hidden}summary{cursor:pointer;padding:16px 18px;font-weight:700;background:rgba(125,211,252,.06)}.content{padding:2px 18px 18px}pre{white-space:pre-wrap;background:#060913;border:1px solid var(--line);padding:14px;border-radius:14px;overflow:auto}.status-ok{color:var(--ok)}.status-warn{color:var(--warn)}.status-bad{color:var(--bad)}hr{border:0;border-top:1px solid var(--line);margin:24px 0}ul,ol{padding-left:1.4rem}code{background:rgba(255,255,255,.08);padding:.12rem .32rem;border-radius:6px}@media (prefers-color-scheme:light){:root{--bg:#f7fafc;--card:#fff;--text:#172033;--muted:#5b6475;--line:#d8e0ee;--accent:#0369a1}body{background:#f7fafc}.hero,.card,details{background:#fff}pre{background:#f8fafc}}
"""

def inline_md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    return s

def md_to_html(md: str) -> str:
    out=[]; in_ul=False; in_ol=False
    def close_lists():
        nonlocal in_ul,in_ol
        if in_ul: out.append('</ul>'); in_ul=False
        if in_ol: out.append('</ol>'); in_ol=False
    for line in md.splitlines():
        raw=line; line=line.rstrip()
        if not line:
            close_lists(); continue
        if line.startswith('# '):
            close_lists(); out.append(f'<h1>{inline_md(line[2:])}</h1>')
        elif line.startswith('## '):
            close_lists(); out.append(f'<h2>{inline_md(line[3:])}</h2>')
        elif line.startswith('### '):
            close_lists(); out.append(f'<h3>{inline_md(line[4:])}</h3>')
        elif line.startswith('#### '):
            close_lists(); out.append(f'<h4>{inline_md(line[5:])}</h4>')
        elif re.match(r'^\d+\. ', line):
            if not in_ol: close_lists(); out.append('<ol>'); in_ol=True
            item_text = re.sub(r'^\d+\. ', '', line)
            out.append(f'<li>{inline_md(item_text)}</li>')
        elif line.startswith('- '):
            if not in_ul: close_lists(); out.append('<ul>'); in_ul=True
            klass=''
            low=line.lower()
            if ' ok' in low or '— ok' in low: klass=' class="status-ok"'
            if 'пусто' in low: klass=' class="status-warn"'
            if 'ошибка' in low: klass=' class="status-bad"'
            out.append(f'<li{klass}>{inline_md(line[2:])}</li>')
        elif line.startswith('   - '):
            if not in_ul: out.append('<ul>'); in_ul=True
            out.append(f'<li>{inline_md(line.strip()[2:])}</li>')
        else:
            close_lists(); out.append(f'<p>{inline_md(line)}</p>')
    close_lists()
    return '\n'.join(out)

def cleanup_old_reports(out_root: Path, keep_days: int, today: str):
    reports = out_root / 'reports'
    if keep_days <= 0 or not reports.exists():
        return []
    cutoff = datetime.strptime(today, '%Y-%m-%d').date() - timedelta(days=keep_days - 1)
    removed=[]
    for child in reports.iterdir():
        if not child.is_dir():
            continue
        try:
            d = datetime.strptime(child.name, '%Y-%m-%d').date()
        except ValueError:
            continue
        if d < cutoff:
            shutil.rmtree(child)
            removed.append(child.name)
    return removed

def build(md_path: Path, raw_path: Path|None, out_root: Path, day: str, keep_days: int = 31):
    removed = cleanup_old_reports(out_root, keep_days, day)
    md=md_path.read_text(encoding='utf-8')
    cjk=re.findall(r'[\u3400-\u9fff]', md)
    day_dir=out_root/'reports'/day
    day_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(md_path, day_dir/'report.md')
    if raw_path and raw_path.exists(): shutil.copy2(raw_path, day_dir/'raw.json')
    body=md_to_html(md)
    cleanup_note = '' if not removed else f'<div class="card meta">Удалены старые отчёты: {html.escape(", ".join(removed))}</div>'
    warning = '' if not cjk else f'<div class="card status-warn">Внимание: найдено CJK-символов: {len(cjk)}. Проверь перевод.</div>'
    page=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>News report {html.escape(day)}</title><style>{CSS}</style></head><body><main><section class="hero"><h1>Утренний отчёт</h1><div class="meta">Дата: {html.escape(day)} · Источник: OpenClaw news-aggregator-skill · <a href="./report.md">Markdown</a> · <a href="./raw.json">Raw JSON</a></div></section>{cleanup_note}{warning}<section class="card">{body}</section></main></body></html>'''
    (day_dir/'index.html').write_text(page,encoding='utf-8')
    # landing redirect-ish latest
    latest=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=reports/{html.escape(day)}/"><title>Latest news report</title><style>{CSS}</style></head><body><main><section class="hero"><h1>Последний отчёт</h1><p><a href="reports/{html.escape(day)}/">Открыть отчёт за {html.escape(day)}</a></p></section></main></body></html>'''
    (out_root/'index.html').write_text(latest,encoding='utf-8')
    return day_dir/'index.html'

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--md', required=True)
    ap.add_argument('--raw')
    ap.add_argument('--out', default='public')
    ap.add_argument('--date', default=date.today().isoformat())
    ap.add_argument('--keep-days', type=int, default=31, help='Keep only reports from the last N days in public/reports')
    args=ap.parse_args()
    result=build(Path(args.md), Path(args.raw) if args.raw else None, Path(args.out), args.date, args.keep_days)
    print(result)
