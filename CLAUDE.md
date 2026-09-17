# bulevo-harness

A harness for Claude Code: plugins, skills, subagents and hooks that make coding agents follow a team's
standards, plus the tooling that measures whether each harness change actually helps.

Before designing or changing a skill, subagent or hook, read `docs/requirements.md`: what the harness
must make agents do and why.

## Layout

- `.claude-plugin/marketplace.json` + `plugins/` — what gets installed into projects. Only this ships to users.
  `plugins/bulevo`: `/bulevo:task` turns a task into an agreed spec in `.claude/tasks/` before code, using
  the read-only `scout` subagent on Sonnet to map existing code. Settings: `.claude/bulevo.json` in the
  project (`pushback`: `quiet` | `balanced` | `strict`).
- Plugin `version` is intentionally unset while iterating, so every pushed commit is an update.
- `tools/transcripts/` — mine Claude Code session transcripts for agent failures: `extract.py` →
  `batch.py` → parallel labeling agents per `LABELING.md` → `report.py`. Stdlib Python, Windows and Linux.
- `evals/` — measurement. `evals/spike/` is a throwaway spike: a probe plugin and a Harbor agent subclass.
- `.claude/skills/` — runbooks for maintaining this repo (`/label-sessions`, `/eval-spike`), not part of
  any plugin.
- `.data/` — mined transcripts, labels and run results. Gitignored because it holds source code and private
  data from the machine it ran on. Never commit it or paste its contents elsewhere.

## Principles

- Measure before adding mechanisms. A harness change is accepted only with evidence: public benchmarks for
  coding regression, a private trap-task suite for behaviors (clarifying questions, pushback on flawed
  requirements, verification, UI, reuse, simplicity, data leaks), and correction metrics from real sessions.
- Past sessions are a map of failures, not benchmark tasks.
- Eval answers, graders for trap tasks and held-out tasks never live in this public repo.
- Rules follow observed failures. Prefer enforcement (types, lint, hooks, tests) over prose in CLAUDE.md,
  and keep hooks non-blocking or give them an exit: gates the agent can neither pass nor change cause loops.
- Agents follow existing project patterns by default and propose a fresh approach only as an explicit
  alternative at design time.
- Verify Claude Code behavior in the current docs or with a cheap `claude -p` experiment before relying on
  it. Mark untested claims as untested.

## Eval findings so far

- Harbor runs Claude Code with a plugin through `evals/spike/bulevo_agent.py`. Its stock agent installs
  nodejs/npm via apt on non-Alpine images and can exceed the 360 s setup timeout, so the harness-off arm of
  a comparison should use the same subclass without a plugin.
- `AskUserQuestion` is unavailable in headless `claude -p` and through Harbor's ACP bridge. Agents ask in
  plain text, so grade clarifying questions from text.
- `claude plugin eval` works with a subscription OAuth token on Linux with bubblewrap and socat.
- Run evals on Linux (WSL2 or native) with Docker. Keep concurrency low: host memory, not the Docker VM,
  is the usual limit.
