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

Run the `label-batches` workflow in this repository, passing the output directory and the number of
`batch-*.txt` files `batch.py` actually created (it makes fewer than asked when there are few sessions):

```
Workflow: name "label-batches", args { "out": "<out>", "batches": <N> }
```

It runs one Sonnet agent per batch against `LABELING.md`, and re-runs any batch that wrote fewer labels
than it had ids, up to twice. Digests stay inside the agents: only counts and a few patterns per batch come
back. Watch it with `/workflows`. If the run reports a batch as still short or lost, finish that batch
yourself before the report.

## 4. Report

```bash
python3 tools/transcripts/report.py --data <out> > <out>/report.json
```

Spot-check two labels against their digests yourself: one with corrections, one without. Then summarize
for the user in their language: outcomes, corrections per session, top correction categories with 2–3 examples
each, what would have prevented them, and the recurring patterns the batch agents reported. Quote the
user's words only as short evidence, and never paste code from digests into the summary.
