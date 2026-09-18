---
name: progress
description: Rebuild and republish the harness progress page from the metrics in /bulevo:retro files. Use when the user asks for the progress page, harness metrics or how the harness is doing.
disable-model-invocation: true
argument-hint: "[path to another machine's tasks JSON]..."
---

# Progress

1. Build the data and the page. Use Python 3 (`py -3` on Windows, `python3` elsewhere):

   ```bash
   <python> tools/retros/progress.py --out .data/progress/tasks.json --html .data/progress/progress.html --extra <each file from $ARGUMENTS and every .data/progress/*.json except tasks.json>
   ```

   Retros without metrics frontmatter are skipped and listed; mention them.

2. Publish `.data/progress/progress.html` with the Artifact tool. If `CLAUDE.local.md` names a progress page
   URL, pass it as `url` so the same page updates; otherwise publish a new page and suggest adding its URL
   there.

3. Summarize in the user's language, in three or four sentences: tasks counted, corrections per task for the
   latest tasks against the earlier ones, how tasks run through `/bulevo:implement` compare with the rest,
   and the most frequent cause. Don't claim a trend from fewer than three tasks per group.

To add another machine: run step 1 there with `--out` only and copy the JSON (numbers and categories, no
task text) into `.data/progress/` here.
