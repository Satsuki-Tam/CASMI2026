"""Fetch a Kaggle competition's official pages, metadata and discussion threads via the public API.

Kaggle web pages are JS-rendered, but the official API (kagglesdk, bundled with the kaggle CLI) exposes:
  competitions API : get_competition, list_competition_pages, list_competition_topics (ids/votes/sticky; no authors)
  discussions API  : get_topic (author + body), list_comments (authors, nested replies)
Authentication comes from the kaggle CLI credentials (~/.kaggle).

Usage:
  python -I -X utf8 src/fetch_kaggle_info.py <competition-slug> <out_dir> [--top N] [--topics ID ...] [--limit CHARS]

Outputs:
  <out_dir>/competition_meta.json      metadata (deadlines, team size, daily submissions, licence, ...)
  <out_dir>/pages/<name>.md            official pages (description, evaluation, rules, data-description, ...)
  <out_dir>/discussion_topics.json     all discussion topics (authors filled in for fetched threads)
  <out_dir>/discussion/<id>_<title>.md thread contents (author per post; host posts flagged) for pinned + top-N + requested topics
"""
import argparse
import html
import time
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.competitions.types import competition_api_service as T
from kagglesdk.discussions.types import discussions_api_service as D


def dump(o):
    return o.to_dict() if hasattr(o, "to_dict") else str(o)


def retry(fn, *args, tries=7, base=8.0):
    """Retry a Kaggle API call on HTTP 429 with linear backoff."""
    for i in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if "429" in str(e) and i < tries - 1:
                time.sleep(base * (i + 1)); continue
            raise


def _link(m):
    href, label = m.group(1), m.group(2)
    return label if label.strip() in href else f"{label} ({href})"


def strip_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>", "\n", s or "")
    s = re.sub(r"<li>", "- ", s)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', _link, s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def fetch_comments(disc, topic_id):
    out, token = [], None
    while True:
        req = D.ApiListCommentsRequest()
        req.topic_id = topic_id
        req.page_size = 100
        if token:
            req.page_token = token
        resp = retry(disc.list_comments, req)
        out.extend(dump(c) for c in (resp.comments or []))
        token = getattr(resp, "next_page_token", None)
        if not token:
            break
    return out


def render_comment(c, labels, depth=0):
    ind = "    " * depth
    name = c.get("authorName") or "?"
    flag = f" **[{labels[name]}]**" if name in labels else ""
    head = f"{ind}- **{name}**{flag} ({str(c.get('postDate', ''))[:10]}, votes {c.get('votes', 0)})"
    body = strip_html(c.get("content") or "").replace("\n", f"\n{ind}  ")
    lines = [f"{head}\n{ind}  {body}\n"]
    for r in c.get("replies") or []:
        lines.append(render_comment(r, labels, depth + 1))
    return "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("competition")
    ap.add_argument("out_dir")
    ap.add_argument("--top", type=int, default=10, help="also fetch the N most-voted topics")
    ap.add_argument("--topics", type=int, nargs="*", default=[], help="explicit topic ids to fetch")
    ap.add_argument("--limit", type=int, default=2500, help="chars printed per thread")
    ap.add_argument("--staff", nargs="*", default=[], help="extra Name=Label pairs to flag, e.g. inversion=Kaggle")
    ap.add_argument("--skip-existing", action="store_true", help="skip topics whose .md already exists")
    ap.add_argument("--pause", type=float, default=1.5, help="seconds to sleep between topics (rate limit)")
    args = ap.parse_args()
    out = pathlib.Path(args.out_dir)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    (out / "discussion").mkdir(exist_ok=True)

    api = KaggleApi()
    api.authenticate()
    with api.build_kaggle_client() as kaggle:
        comp = kaggle.competitions.competition_api_client
        disc = kaggle.discussions.discussion_api_client

        req = T.ApiGetCompetitionRequest()
        req.competition_name = args.competition
        meta = dump(comp.get_competition(req))
        (out / "competition_meta.json").write_text(json.dumps(meta, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
        print("== competition:", meta.get("title"), "| deadline", meta.get("deadline"), "| team<=", meta.get("maxTeamSize"),
              "| subs/day", meta.get("maxDailySubmissions"), "| teams", meta.get("teamCount"), "| licence:", meta.get("licenseName"))

        req = T.ApiListCompetitionPagesRequest()
        req.competition_name = args.competition
        pages = [dump(p) for p in comp.list_competition_pages(req).pages]
        for p in pages:
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", p.get("name") or "page")
            (out / "pages" / f"{name}.md").write_text(p.get("content") or "", encoding="utf-8")
        print("== pages:", ", ".join(f"{p.get('name')}({len(p.get('content') or ''):,})" for p in pages))

        topics, page = {}, 1
        while True:
            req = T.ApiListCompetitionTopicsRequest()
            req.competition_name = args.competition
            req.page = page
            resp = comp.list_competition_topics(req)
            rows = [dump(t) for t in resp.topics]
            if not rows:
                break
            for r in rows:
                topics[r.get("id")] = r
            total = getattr(resp, "total_count", None)
            if (total is not None and len(topics) >= total) or page > 200:
                break
            page += 1
        print(f"== topics: {len(topics)}")

        def votes(r):
            return r.get("votes") or 0

        sticky = [r for r in topics.values() if r.get("isSticky")]
        wanted = sticky + sorted(topics.values(), key=lambda r: -votes(r))[: args.top]
        wanted += [topics[i] for i in args.topics if i in topics]
        for i in args.topics:
            if i not in topics:
                print(f"!! topic {i} not found in list")

        # host names = authors of pinned topics (competition hosts / Kaggle staff pin the announcements)
        hosts = set()
        for r in sticky:
            try:
                g = D.ApiGetTopicRequest()
                g.id = r["id"]
                t = dump(retry(disc.get_topic, g).topic)
                r.update({"authorName": t.get("authorName"), "authorUrl": t.get("authorUrl")})
                if t.get("authorName"):
                    hosts.add(t["authorName"])
            except Exception as e:
                print(f"!! get_topic {r['id']} failed: {repr(e)[:120]}")
        print("== pinned-topic authors (flagged HOST):", sorted(hosts))
        labels = {n: "HOST" for n in hosts}
        for s in args.staff:
            n, _, lab = s.partition("=")
            labels[n] = lab or "STAFF"

        seen = set()
        for r in wanted:
            tid = r.get("id")
            if tid in seen:
                continue
            seen.add(tid)
            slug0 = re.sub(r"[^A-Za-z0-9._-]+", "_", str(r.get("title")))[:60]
            if args.skip_existing and (out / "discussion" / f"{tid}_{slug0}.md").exists():
                continue
            time.sleep(args.pause)
            try:
                g = D.ApiGetTopicRequest()
                g.id = tid
                t = dump(retry(disc.get_topic, g).topic)
                comments = fetch_comments(disc, tid)
            except Exception as e:
                print(f"\n!! topic {tid} failed: {repr(e)[:200]}")
                continue
            r.update({"authorName": t.get("authorName"), "authorUrl": t.get("authorUrl")})
            slug = re.sub(r"[^A-Za-z0-9._-]+", "_", str(r.get("title")))[:60]
            author = t.get("authorName") or "?"
            flag = f" **[{labels[author]}]**" if author in labels else ""
            header = (f"topic {tid} | by **{author}**{flag} ({t.get('authorUrl', '')}) | posted {str(t.get('postDate', ''))[:10]} | "
                      f"votes {t.get('votes', 0)} | comments {t.get('commentCount', 0)} | https://www.kaggle.com{t.get('url', '')}\n")
            md = [f"# {t.get('title')}\n", header, f"\n{strip_html(t.get('content') or '')}\n", f"\n## Comments ({len(comments)} top-level)\n\n"]
            md += [render_comment(c, labels) for c in sorted(comments, key=lambda c: str(c.get("postDate", "")))]
            text = "".join(md)
            (out / "discussion" / f"{tid}_{slug}.md").write_text(text, encoding="utf-8")
            (out / "discussion" / f"{tid}_{slug}.json").write_text(
                json.dumps({"topic": t, "comments": comments}, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
            tail = "...[truncated]" if len(text) > args.limit else ""
            print("\n" + "#" * 90 + "\n" + text[: args.limit] + tail)

        (out / "discussion_topics.json").write_text(json.dumps(list(topics.values()), indent=2, default=str, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
