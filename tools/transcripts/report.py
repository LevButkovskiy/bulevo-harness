#!/usr/bin/env python3
"""Join transcripts.py metrics with agent labels and print aggregates as JSON.

Usage:
  python tools/transcripts/report.py --data .data/stage0 > .data/stage0/report.json
"""
import argparse
import collections
import glob
import json
import os
import re
import sys


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def total_tokens(tokens, kinds=("in", "out", "cache_read", "cache_write")):
    return sum(v.get(k, 0) for v in tokens.values() for k in kinds)


def short_project(p):
    # "C--Projects-acme-shop" or "-home-dev-projects-api-gateway" -> "acme-shop" / "api-gateway"
    p = p.split("--claude-worktrees")[0]
    return re.sub(r"^.*?[Pp]rojects-", "", p) or p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    sessions = {s["session_id"]: s for s in load_jsonl(os.path.join(args.data, "sessions.jsonl"))}
    labels = {}
    for f in glob.glob(os.path.join(args.data, "labels", "*.jsonl")):
        for lab in load_jsonl(f):
            labels[lab["session_id"]] = lab

    rows = []
    for sid, s in sessions.items():
        lab = labels.get(sid)
        if not lab:
            continue
        rows.append({**s, "label": lab, "project_short": short_project(s["project"])})

    by = lambda key: collections.Counter(key(r) for r in rows)
    corrections = [(r, c) for r in rows for c in r["label"].get("corrections", [])]
    corr_cat = collections.Counter(c["category"] for _, c in corrections)
    corr_fix = collections.Counter(c["harness_fix"] for _, c in corrections)

    per_project = collections.defaultdict(lambda: {"sessions": 0, "corrections": 0, "active_hours": 0.0,
                                                   "output_tokens": 0, "cache_read_tokens": 0})
    for r in rows:
        p = per_project[r["project_short"]]
        p["sessions"] += 1
        p["corrections"] += len(r["label"].get("corrections", []))
        p["active_hours"] = round(p["active_hours"] + r["active_minutes"] / 60, 1)
        p["output_tokens"] += total_tokens(r["tokens_main"], ("out",)) + total_tokens(r["tokens_subagents"], ("out",))
        p["cache_read_tokens"] += total_tokens(r["tokens_main"], ("cache_read",)) + total_tokens(r["tokens_subagents"], ("cache_read",))

    def card(r):
        lab = r["label"]
        return {
            "session_id": r["session_id"],
            "project": r["project_short"],
            "start": (r["start"] or "")[:10],
            "summary": lab["summary"],
            "type": lab["type"],
            "size": lab["size"],
            "outcome": lab["outcome"],
            "prompts": r["human_prompts"],
            "active_min": r["active_minutes"],
            "commits": len(r["commits"]),
            "corrections": len(lab.get("corrections", [])),
            "why": lab["benchmark_candidate"]["why"],
            "verifiable_by": lab["benchmark_candidate"]["verifiable_by"],
            "fit": lab["benchmark_candidate"]["fit"],
        }

    candidates = sorted((card(r) for r in rows if r["label"]["benchmark_candidate"]["fit"] in ("strong", "possible")),
                        key=lambda c: (c["fit"] != "strong", -c["corrections"], -c["active_min"]))

    report = {
        "labeled": len(rows),
        "unlabeled": sorted(set(sessions) - set(labels)),
        "period": [min(r["start"] for r in rows)[:10], max(r["end"] for r in rows)[:10]] if rows else None,
        "active_hours": round(sum(r["active_minutes"] for r in rows) / 60),
        "types": by(lambda r: r["label"]["type"]).most_common(),
        "sizes": by(lambda r: r["label"]["size"]).most_common(),
        "outcomes": by(lambda r: r["label"]["outcome"]).most_common(),
        "task_clarity": by(lambda r: r["label"]["task_clarity"]).most_common(),
        "agent_questions_useful": by(lambda r: r["label"]["agent_questions_useful"]).most_common(),
        "agent_pushback": by(lambda r: r["label"]["agent_pushback"]).most_common(),
        "sessions_with_corrections": sum(1 for r in rows if r["label"].get("corrections")),
        "corrections_total": len(corrections),
        "correction_categories": corr_cat.most_common(),
        "correction_harness_fix": corr_fix.most_common(),
        "correction_examples": {
            cat: [{"project": r["project_short"], "evidence": c["evidence"], "fix": c["harness_fix"]}
                  for r, c in corrections if c["category"] == cat][:6]
            for cat, _ in corr_cat.most_common(8)
        },
        "interruptions_sessions": sum(1 for r in rows if r["interruptions"]),
        "per_project": dict(sorted(per_project.items(), key=lambda kv: -kv[1]["sessions"])),
        "candidates": candidates,
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
