#!/usr/bin/env python3
"""Collect the metrics frontmatter of /bulevo:retro files into one JSON list, optionally rendered as a page.

Retros stay on the machine where the task ran. Run this on each machine and pass the other machines' JSON
with --extra to combine them. Only the numeric and categorical fields are read, never the retro text.

Usage:
  python tools/retros/progress.py --out .data/progress/tasks.json
  python tools/retros/progress.py --extra server-tasks.json --html .data/progress/progress.html
"""
import argparse
import glob
import json
import os
import sys

FIELDS = ("date", "started", "project", "size", "type", "skills", "implemented_via", "corrections_spec",
          "corrections_impl", "causes", "understanding", "questions", "code_found", "spec", "active_min",
          "cache_read_m", "output_k")
NUMBERS = ("corrections_spec", "corrections_impl", "active_min", "cache_read_m", "output_k")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress_page.html")


def default_dirs():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return glob.glob(os.path.join(base, "plugins", "data", "*", "retros"))


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [x.strip().strip("'\"") for x in raw[1:-1].split(",") if x.strip()]
    return raw.strip("'\"")


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = parse_value(value)
    return data


def record(meta, source):
    rec = {key: meta.get(key) for key in FIELDS}
    for key in NUMBERS:
        try:
            rec[key] = float(rec[key]) if rec[key] not in (None, "") else None
        except ValueError:
            rec[key] = None
    rec["source"] = source
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", action="append", default=[], help="retros folder (default: plugin data folders)")
    ap.add_argument("--extra", action="append", default=[], help="JSON list from another machine")
    ap.add_argument("--out", help="write the combined JSON here")
    ap.add_argument("--html", help="write a self-contained progress page here")
    ap.add_argument("--baseline", type=float,
                    help="corrections per task before the harness, drawn as a line; must be per task from retros")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    tasks = []
    for folder in args.dir or default_dirs():
        for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
            meta = frontmatter(path)
            if meta.get("corrections_impl") is None and meta.get("corrections_spec") is None:
                print(f"skipped, no metrics: {os.path.basename(path)}", file=sys.stderr)
                continue
            tasks.append(record(meta, os.path.basename(path)))
    for path in args.extra:
        with open(path, encoding="utf-8") as fh:
            tasks.extend(json.load(fh))
    tasks.sort(key=lambda t: t.get("started") or t.get("date") or "")

    payload = json.dumps(tasks, ensure_ascii=False, indent=1)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
    if args.html:
        with open(TEMPLATE, encoding="utf-8") as fh:
            page = fh.read().replace("/*TASKS*/[]", payload)
        page = page.replace("/*BASELINE*/null", json.dumps(args.baseline))
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(page)
    if not args.out and not args.html:
        print(payload)
    print(f"{len(tasks)} tasks", file=sys.stderr)


if __name__ == "__main__":
    main()
