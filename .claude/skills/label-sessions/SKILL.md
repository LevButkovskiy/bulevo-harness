---
name: label-sessions
description: Mine and label this machine's Claude Code session transcripts to find where agents failed. Use when the user asks to analyze, label or review past sessions or transcripts.
disable-model-invocation: true
argument-hint: "[--skip <project-substring>]..."
---

# Label sessions

Analyze this machine's Claude Code transcripts with the scripts in `tools/transcripts/`.
Raw transcripts, digests and labels contain source code and private data: everything stays under
`.data/`, which is gitignored. Never commit it and never copy its contents anywhere else.

## 1. Extract

Pick a Python 3 interpreter (`python3`, else `python`). Choose an output directory named after this
machine and today's date, for example `.data/<hostname>-<YYYY-MM-DD>`.

```bash
python3 plugins/bulevo/scripts/transcripts.py --out <out> --skip bulevo-harness $ARGUMENTS
```

Report the session count per project from `<out>/sessions.jsonl` and ask the user whether to exclude any
project before labeling, for example scratch directories like `-tmp`. If they exclude one, rerun extract
with an extra `--skip`.

## 2. Batch

Aim for about 240 KB of digests per batch:

```bash
python3 tools/transcripts/batch.py --data <out> --batches <N>
```

## 3. Label in parallel

Launch one subagent per batch in a single message, each with `model: "sonnet"`, running in the background.
Give each this prompt, with the batch number and output directory filled in:

> Label Claude Code session digests. Repo root: the current directory.
> 1. Read the rules: tools/transcripts/LABELING.md — follow them exactly.
> 2. Session ids to label (one per line): <out>/batches/batch-<i>.txt
> 3. For each id read <out>/digests/<id>.md in full (use Read with offset/limit for large files; don't skip
>    parts — corrections often appear late).
> 4. Write exactly one JSON line per session to <out>/labels/batch-<i>.jsonl (valid JSON per line, UTF-8,
>    same key order as the rules). Write incrementally so progress isn't lost.
> 5. Do not read raw transcripts under ~/.claude and do not modify anything else.
> When done, check every line parses as JSON and the line count equals the id count. Reply with only: count
> labeled, and 2–3 notable patterns across the batch (short, in the language the user writes in).

Wait for every batch. If one comes back short, send that agent a follow-up to finish the missing ids.

## 4. Report

```bash
python3 tools/transcripts/report.py --data <out> > <out>/report.json
```

Spot-check two labels against their digests yourself: one with corrections, one without. Then summarize
for the user in their language: outcomes, corrections per session, top correction categories with 2–3 examples
each, what would have prevented them, and the recurring patterns the batch agents reported. Quote the
user's words only as short evidence, and never paste code from digests into the summary.
