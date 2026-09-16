#!/usr/bin/env python3
"""Extract per-session facts and a compact dialogue digest from Claude Code transcripts.

Stdlib only, so it runs unchanged on Windows and on a Linux dev server.

Output (under --out):
  sessions.jsonl        one JSON object of hard metrics per session
  digests/<id>.md       human prompts plus a short trace of what the agent did between them

Usage:
  python tools/transcripts/extract.py --out .data/stage0
  python tools/transcripts/extract.py --projects-dir ~/.claude/projects --skip bulevo-harness --out .data/stage0
"""
import argparse
import collections
import glob
import json
import os
import re
import sys
from datetime import datetime

PROMPT_LIMIT = 1500
REPLY_LIMIT = 700
LONG_SESSION_TURNS = 40  # beyond this, digests clip harder to stay readable for a labeling agent
IDLE_GAP_SECONDS = 300  # a pause longer than this between events is not counted as active time
INTERRUPT = "[Request interrupted by user"
REJECT = "doesn't want to proceed"


def parse_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def clip(s, limit):
    s = s.strip()
    return s if len(s) <= limit else s[:limit] + f" …[+{len(s) - limit} chars]"


def commit_subject(cmd):
    # heredoc message: `git commit -F - <<'MSG'` or `-m "$(cat <<'EOF'`, subject is the first line after the marker
    m = re.search(r"git\b[^\n]*\bcommit\b[^\n]*<<-?\s*['\"]?\w+['\"]?\)?\s*\n\s*([^\n]{1,120})", cmd)
    if not m:
        m = re.search(r"-m\s+[\"']([^\"'\n]{1,120})", cmd)
    return m.group(1).strip() if m else clip(cmd, 120)


def read_jsonl(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def usage_add(counter, model, usage):
    counter[(model, "out")] += usage.get("output_tokens", 0)
    counter[(model, "in")] += usage.get("input_tokens", 0)
    counter[(model, "cache_read")] += usage.get("cache_read_input_tokens", 0)
    counter[(model, "cache_write")] += usage.get("cache_creation_input_tokens", 0)


def tokens_by_model(counter):
    out = collections.defaultdict(dict)
    for (model, kind), v in counter.items():
        if v:
            out[model or "unknown"][kind] = v
    return dict(out)


def extract_session(path, project):
    sid = os.path.splitext(os.path.basename(path))[0]
    first_ts = last_ts = None
    cwd = branch = version = entrypoint = None
    turns = []  # each: {"prompt", "ts", "tools": Counter, "reply", "interrupted", "rejected", "errors"}
    tools_total = collections.Counter()
    tok = collections.Counter()
    commits = []
    active_ms = 0
    prev_ts = None
    compactions = 0
    stop_hook_goals = set()
    api_errors = 0
    task_notifications = 0
    permission_modes = collections.Counter()

    def cur():
        if not turns:
            turns.append({"prompt": "(no human prompt yet)", "ts": None, "tools": collections.Counter(),
                          "reply": "", "interrupted": 0, "rejected": 0, "errors": 0})
        return turns[-1]

    for d in read_jsonl(path):
        ts = d.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
            now = parse_ts(ts)
            if prev_ts and now:
                gap = (now - prev_ts).total_seconds()
                if 0 < gap <= IDLE_GAP_SECONDS:
                    active_ms += gap * 1000
            prev_ts = now or prev_ts
        cwd = cwd or d.get("cwd")
        branch = branch or d.get("gitBranch")
        version = d.get("version") or version
        entrypoint = entrypoint or d.get("entrypoint")
        typ = d.get("type")

        if typ == "system":
            st = d.get("subtype")
            if st == "compact_boundary":
                compactions += 1
            elif st == "api_error":
                api_errors += 1
            elif st == "stop_hook_summary":
                for h in d.get("hookInfos") or []:
                    if h.get("promptText"):
                        stop_hook_goals.add(clip(h["promptText"], 300))
            continue

        if typ == "user" and not d.get("isSidechain"):
            msg = d.get("message") or {}
            content = msg.get("content")
            kind = (d.get("origin") or {}).get("kind")
            if d.get("permissionMode"):
                permission_modes[d["permissionMode"]] += 1
            if kind == "task-notification":
                task_notifications += 1
                continue
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        body = b.get("content")
                        body = text_of(body) if not isinstance(body, str) else body
                        if REJECT in body:
                            cur()["rejected"] += 1
                        elif b.get("is_error"):
                            cur()["errors"] += 1
            txt = text_of(content)
            if INTERRUPT in txt:
                cur()["interrupted"] += 1
                continue
            if kind == "human" and not d.get("isMeta") and txt.strip():
                turns.append({"prompt": txt, "ts": ts, "tools": collections.Counter(), "reply": "",
                              "interrupted": 0, "rejected": 0, "errors": 0})
            continue

        if typ == "assistant":
            msg = d.get("message") or {}
            usage_add(tok, msg.get("model"), msg.get("usage") or {})
            if d.get("isSidechain"):
                continue
            for b in msg.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    name = b.get("name", "?")
                    cur()["tools"][name] += 1
                    tools_total[name] += 1
                    cmd = (b.get("input") or {}).get("command", "")
                    if isinstance(cmd, str) and re.search(r"\bgit\b[^|;&\n]*\bcommit\b", cmd):
                        commits.append(commit_subject(cmd))
                elif b.get("type") == "text" and b.get("text", "").strip():
                    cur()["reply"] = b["text"]

    # subagent transcripts live next to the session file
    sub_dir = os.path.join(os.path.dirname(path), sid, "subagents")
    sub_files = glob.glob(os.path.join(sub_dir, "*.jsonl"))
    sub_tok = collections.Counter()
    for sf in sub_files:
        for d in read_jsonl(sf):
            if d.get("type") == "assistant":
                msg = d.get("message") or {}
                usage_add(sub_tok, msg.get("model"), msg.get("usage") or {})

    human_turns = [t for t in turns if t["ts"]]
    t0, t1 = parse_ts(first_ts), parse_ts(last_ts)
    main_models = collections.Counter()
    for (model, kind), v in tok.items():
        if kind == "out" and model:
            main_models[model] += v

    meta = {
        "session_id": sid,
        "project": project,
        "cwd": cwd,
        "branch": branch,
        "entrypoint": entrypoint,
        "cc_version": version,
        "start": first_ts,
        "end": last_ts,
        "wall_minutes": round((t1 - t0).total_seconds() / 60, 1) if t0 and t1 else None,
        "active_minutes": round(active_ms / 60000, 1),  # sum of event gaps <= IDLE_GAP_SECONDS
        "human_prompts": len(human_turns),
        "interruptions": sum(t["interrupted"] for t in turns),
        "permission_rejections": sum(t["rejected"] for t in turns),
        "tool_errors": sum(t["errors"] for t in turns),
        "compactions": compactions,
        "api_errors": api_errors,
        "task_notifications": task_notifications,
        "tool_calls": sum(tools_total.values()),
        "tools": dict(tools_total.most_common()),
        "ask_user_question": tools_total.get("AskUserQuestion", 0),
        "subagent_calls": tools_total.get("Agent", 0) + tools_total.get("Task", 0),
        "subagent_transcripts": len(sub_files),
        "commits": commits,
        "stop_hook_goals": sorted(stop_hook_goals),
        "permission_modes": dict(permission_modes),
        "main_model": main_models.most_common(1)[0][0] if main_models else None,
        "tokens_main": tokens_by_model(tok),
        "tokens_subagents": tokens_by_model(sub_tok),
    }
    return meta, turns


def digest(meta, turns):
    lines = [
        f"# Session {meta['session_id']}",
        f"project: {meta['project']} | cwd: {meta['cwd']} | branch: {meta['branch']}",
        f"start: {meta['start']} | wall: {meta['wall_minutes']} min | active: {meta['active_minutes']} min",
        f"human prompts: {meta['human_prompts']} | tool calls: {meta['tool_calls']} | "
        f"interruptions: {meta['interruptions']} | rejections: {meta['permission_rejections']} | "
        f"compactions: {meta['compactions']} | subagents: {meta['subagent_calls']} | AskUserQuestion: {meta['ask_user_question']}",
        f"commits: {len(meta['commits'])}" + (" — " + " | ".join(meta["commits"][:8]) if meta["commits"] else ""),
    ]
    if meta["stop_hook_goals"]:
        lines.append("goals (stop hook): " + " || ".join(meta["stop_hook_goals"]))
    lines.append("")
    long = len(turns) > LONG_SESSION_TURNS
    prompt_limit, reply_limit = (PROMPT_LIMIT // 2, REPLY_LIMIT // 2) if long else (PROMPT_LIMIT, REPLY_LIMIT)
    for i, t in enumerate(turns, 1):
        who = "USER" if t["ts"] else "PRE"
        lines.append(f"## Turn {i} [{who}] {t['ts'] or ''}")
        lines.append(clip(t["prompt"], prompt_limit))
        tools = ", ".join(f"{k}×{v}" for k, v in t["tools"].most_common(8))
        flags = []
        for key, label in (("interrupted", "INTERRUPTED"), ("rejected", "REJECTED-TOOL"), ("errors", "tool-errors")):
            if t[key]:
                flags.append(f"{label}×{t[key]}")
        lines.append(f"→ agent: tools [{tools or 'none'}] {' '.join(flags)}")
        if t["reply"]:
            lines.append("→ last reply: " + clip(t["reply"], reply_limit))
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", action="append", default=[], help="substring of project dir name to skip")
    ap.add_argument("--min-prompts", type=int, default=1)
    ap.add_argument("--min-tool-calls", type=int, default=1,
                    help="skip noise sessions such as pings or runs that died on connection errors before any work")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(os.path.join(args.out, "digests"), exist_ok=True)
    count = skipped = 0
    with open(os.path.join(args.out, "sessions.jsonl"), "w", encoding="utf-8") as out:
        for path in sorted(glob.glob(os.path.join(args.projects_dir, "*", "*.jsonl"))):
            project = os.path.basename(os.path.dirname(path))
            if any(s in project for s in args.skip):
                continue
            meta, turns = extract_session(path, project)
            if meta["human_prompts"] < args.min_prompts or meta["tool_calls"] < args.min_tool_calls:
                skipped += 1
                continue
            out.write(json.dumps(meta, ensure_ascii=False) + "\n")
            with open(os.path.join(args.out, "digests", meta["session_id"] + ".md"), "w", encoding="utf-8") as fh:
                fh.write(digest(meta, turns))
            count += 1
    print(f"{count} sessions -> {args.out} ({skipped} skipped as noise)")


if __name__ == "__main__":
    main()
