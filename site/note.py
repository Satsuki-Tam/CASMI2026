"""Append an event to the dashboard log and rebuild the site.
Usage: python -X utf8 site/note.py "text" [--kind event|result|decision|issue|submit] [--link page.html]
"""
import argparse, datetime as dt, json, os, subprocess, sys

SITE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("text"); ap.add_argument("--kind", default="event"); ap.add_argument("--link", default=None); ap.add_argument("--time", default=None)
a = ap.parse_args()
ev = dict(time=a.time or dt.datetime.now().strftime("%Y-%m-%d %H:%M"), kind=a.kind, text=a.text)
if a.link: ev["link"] = a.link
with open(os.path.join(SITE, "events.jsonl"), "a", encoding="utf-8") as f: f.write(json.dumps(ev, ensure_ascii=False) + "\n")
subprocess.run([sys.executable, "-X", "utf8", os.path.join(SITE, "build_site.py")], check=False)
