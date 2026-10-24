"""Render the static dashboard under site/ from the docs, the Codex review files and the event log.

Pages: index.html (now: goal status, running jobs, latest events, next decisions), experiments.html (+ one page per document),
research.html, codex.html, submissions.html, competition.html. Pure static HTML, no external assets; index auto-refreshes.
Usage: python -X utf8 site/build_site.py
"""
import datetime as dt, html, json, os, re, sys
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SITE = os.path.join(ROOT, "site")
MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"toc_depth": "2-3"}})
NAV = [("index.html", "いま"), ("overview.html", "課題の全体像"), ("eda.html", "データの詳細"), ("experiments.html", "実験"), ("research.html", "調査"), ("validation.html", "検証設計"), ("codex.html", "Codex 議論"), ("submissions.html", "提出"), ("competition.html", "コンペ概要")]
CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1f2328;--muted:#6b7280;--line:#e5e7eb;--acc:#0b6e4f;--warn:#b45309;--bad:#b91c1c}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI","Hiragino Sans","Noto Sans JP",sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:#fff;border-bottom:1px solid var(--line);padding:10px 20px;display:flex;gap:18px;align-items:baseline;flex-wrap:wrap;position:sticky;top:0;z-index:2}
header .title{font-weight:700;margin-right:10px}header a{color:var(--ink);text-decoration:none;padding:4px 8px;border-radius:6px}header a.on{background:var(--acc);color:#fff}
main{max-width:1180px;margin:0 auto;padding:18px 20px 60px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}.card h2{margin:0 0 8px;font-size:1.05rem}
.kpi{display:flex;gap:22px;flex-wrap:wrap}.kpi div{min-width:120px}.kpi .v{font-size:1.5rem;font-weight:700}.kpi .l{color:var(--muted);font-size:.85rem}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{background:#fafafa}
.ev{border-left:3px solid var(--line);padding:4px 10px;margin:6px 0}.ev.decision{border-color:var(--acc)}.ev.result{border-color:#2563eb}.ev.issue{border-color:var(--bad)}.ev.submit{border-color:var(--warn)}
.ev .t{color:var(--muted);font-size:.8rem;margin-right:8px}.muted{color:var(--muted)}.badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:.78rem;background:#eef2ff}
.badge.run{background:#dcfce7}.badge.wait{background:#fef9c3}.badge.done{background:#e5e7eb}.badge.fail{background:#fee2e2}
article{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 24px}article h1{font-size:1.4rem}article h2{font-size:1.15rem;border-bottom:1px solid var(--line);padding-bottom:4px;margin-top:28px}
article table{display:block;overflow-x:auto}details{margin:8px 0}summary{cursor:pointer;font-weight:600}.toc{background:#fafafa;border:1px solid var(--line);border-radius:8px;padding:8px 14px;font-size:.9rem}
code{background:#f3f4f6;padding:1px 4px;border-radius:4px;font-size:.88em}pre{background:#f3f4f6;padding:10px;border-radius:8px;overflow-x:auto}
.small{font-size:.85rem}footer{color:var(--muted);font-size:.8rem;margin-top:30px}
"""


def page(title, body, active, refresh=False):
    nav = "".join(f'<a href="{h}" class="{"on" if h == active else ""}">{t}</a>' for h, t in NAV)
    meta = '<meta http-equiv="refresh" content="60">' if refresh else ""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M JST")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{meta}
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<header><span class="title">CASMI 2026</span>{nav}<span class="muted small" style="margin-left:auto">更新 {now}</span></header>
<main>{body}<footer>生成: site/build_site.py — コード: <a href="https://github.com/Satsuki-Tam/CASMI2026">github.com/Satsuki-Tam/CASMI2026</a></footer></main></body></html>"""


def md_to_html(path):
    text = open(path, encoding="utf-8").read(); MD.reset()
    body = MD.convert(text); toc = MD.toc if MD.toc and MD.toc.count("<li>") > 2 else ""
    return (f'<div class="toc">{toc}</div>' if toc else "") + body


def doc_page(src, out, title, active):
    body = f"<article>{md_to_html(os.path.join(ROOT, src))}</article><p class='small muted'>原文: <code>{src}</code></p>"
    open(os.path.join(SITE, out), "w", encoding="utf-8").write(page(title, body, active))


def load_status():
    return json.load(open(os.path.join(SITE, "status.json"), encoding="utf-8"))


def load_events():
    p = os.path.join(SITE, "events.jsonl")
    ev = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []
    return sorted(ev, key=lambda e: e["time"], reverse=True)


def index(status, events):
    k = status["kpi"]
    kpi = "".join(f'<div><div class="v">{html.escape(str(v))}</div><div class="l">{html.escape(l)}</div></div>' for l, v in k.items())
    jobs = "".join(f'<tr><td><span class="badge {j.get("state","run")}">{j.get("state","run")}</span></td><td>{html.escape(j["name"])}</td><td>{html.escape(j.get("detail",""))}</td><td class="muted small">{html.escape(j.get("eta",""))}</td></tr>' for j in status["jobs"])
    nexts = "".join(f"<li>{html.escape(x)}</li>" for x in status["next"])
    evs = "".join(f'<div class="ev {e.get("kind","")}"><span class="t">{html.escape(e["time"][5:16])}</span>{html.escape(e["text"])}' + (f' <a href="{e["link"]}">詳細</a>' if e.get("link") else "") + "</div>" for e in events[:40])
    links = "".join(f'<li><a href="{h}">{html.escape(t)}</a> — {html.escape(d)}</li>' for h, t, d in status.get("pages", []))
    body = f"""<div class="card"><h2>目標と現在値</h2><div class="kpi">{kpi}</div><p class="small muted">{html.escape(status.get("headline",""))}</p></div>
<div class="grid" style="margin-top:14px">
<div class="card"><h2>進行中の作業</h2><table><tr><th></th><th>作業</th><th>内容</th><th>見込み</th></tr>{jobs}</table></div>
<div class="card"><h2>次の判断ポイント</h2><ol>{nexts}</ol></div></div>
<div class="card" style="margin-top:14px"><h2>出来事(新しい順)</h2>{evs}</div>
<div class="card" style="margin-top:14px"><h2>詳細ページ</h2><ul>{links}</ul></div>"""
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page("CASMI 2026 — いま", body, "index.html", refresh=True))


def experiments(status):
    rows = "".join(f'<tr><td><b>{html.escape(e["id"])}</b></td><td>{html.escape(e["question"])}</td><td>{html.escape(e["result"])}</td><td><code>{html.escape(e["code"])}</code></td><td>' + (f'<a href="{e["page"]}">詳細</a>' if e.get("page") else "") + f'</td><td><span class="badge {e.get("state","done")}">{e.get("state","done")}</span></td></tr>' for e in status["experiments"])
    body = f"""<div class="card"><h2>実験一覧(コード → 結果)</h2><p class="small muted">各行は 1 つの問いに対応する。詳細ページに設計・結果・判断が載る。コードは GitHub の同じパス。</p>
<table><tr><th>ID</th><th>問い</th><th>結果(要点)</th><th>コード</th><th></th><th>状態</th></tr>{rows}</table></div>"""
    open(os.path.join(SITE, "experiments.html"), "w", encoding="utf-8").write(page("実験", body, "experiments.html"))


def codex_page():
    d = os.path.join(ROOT, "reports", "agent_review"); nums = sorted({f[:3] for f in os.listdir(d) if re.match(r"\d{3}_", f)})
    parts = []
    for n in nums:
        sec = []
        for kind, label in (("request", "依頼(Claude Code)"), ("codex", "回答(Codex)"), ("decision", "判断記録(Claude Code)")):
            fp = os.path.join(d, f"{n}_{kind}.md")
            if os.path.exists(fp): sec.append(f"<details><summary>{label}</summary>{md_to_html(fp)}</details>")
        init = os.path.join(d, f"{n}_codex_initial_review.md")
        if os.path.exists(init): sec.append(f"<details><summary>初回レビュー(Codex)</summary>{md_to_html(init)}</details>")
        title = ""
        for kind in ("request", "decision", "codex_initial_review", "codex"):
            fp = os.path.join(d, f"{n}_{kind}.md")
            if os.path.exists(fp):
                first = open(fp, encoding="utf-8").readline().strip("# \n"); title = first; break
        parts.append(f'<article><h1>{n}: {html.escape(title)}</h1>{"".join(sec)}</article>')
    body = '<p class="small muted">Claude Code と Codex の往復。各往復は 依頼 → 回答 → 判断記録 の 3 つで構成(折りたたみ)。</p>' + "".join(parts)
    open(os.path.join(SITE, "codex.html"), "w", encoding="utf-8").write(page("Codex 議論", body, "codex.html"))


def research_page(status):
    items = status.get("research", [])
    cards = "".join(f'<div class="card"><h2><a href="{r["page"]}">{html.escape(r["title"])}</a></h2><p class="small">{html.escape(r["summary"])}</p></div>' for r in items)
    body = f'<p class="small muted">調査は主題ごとに別ページ。要点はカードに、全文はリンク先に。</p><div class="grid">{cards}</div>'
    open(os.path.join(SITE, "research.html"), "w", encoding="utf-8").write(page("調査", body, "research.html"))


def submissions_page(status):
    rows = "".join(f'<tr><td>{html.escape(s["when"])}</td><td><b>{html.escape(s["id"])}</b></td><td>{html.escape(s["what"])}</td><td>{html.escape(str(s["public"]))}</td><td>{html.escape(s["note"])}</td></tr>' for s in status["submissions"])
    body = f'<div class="card"><h2>提出履歴(Public LB)</h2><table><tr><th>日時 (JST)</th><th>ID</th><th>内容</th><th>Public</th><th>読み方</th></tr>{rows}</table><p class="small muted">金圏下限 ≈ 0.473、首位 0.504(2026-10-24 朝)。Public は約 130 分子で ±0.01 の揺らぎ。</p></div>'
    open(os.path.join(SITE, "submissions.html"), "w", encoding="utf-8").write(page("提出", body, "submissions.html"))


def main():
    status = load_status(); events = load_events()
    index(status, events); experiments(status); codex_page(); research_page(status); submissions_page(status)
    for src, out, title in status.get("docs", []):
        active = "research.html" if out.startswith("research_") else ("competition.html" if out == "competition.html" else "experiments.html")
        try: doc_page(src, out, title, active)
        except Exception as e: print("doc failed", src, repr(e))
    print("site built:", dt.datetime.now().strftime("%H:%M:%S"), "| events", len(events))


if __name__ == "__main__":
    main()
