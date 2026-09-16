---
name: eval-spike
description: Hands-on spike that checks whether Harbor and claude plugin eval can measure this harness, run locally in WSL2 Ubuntu with Docker Desktop. Use when the user asks to run the eval spike.
disable-model-invocation: true
---

# Eval spike

Answer six open questions with real runs before building the eval system. Work step by step, stop at
the first blocker, and write findings to `.data/spike/results.md` as you go (create it; `.data/` is
gitignored). Report in Russian.

## Where this runs

The user's Windows workstation, inside WSL2 Ubuntu, with Docker Desktop providing Docker through WSL
integration. The user starts Claude Code from an Ubuntu terminal in a clone of this repo that lives on
the WSL filesystem (for example `~/projects/bulevo-harness`), not under `/mnt/<drive>/`: the Windows
checkout has CRLF line endings that break shell scripts, and `/mnt` I/O is slow.

## Ground rules

- **Workstation in use.** The user keeps working on this PC. Use concurrency 1 for agent runs (2 only for
  the model-free oracle run) and stop if the Docker VM's free memory drops below 4 GB or the disk holding
  Docker's data has less than 30 GB free.
- **Subscription only.** Use `CLAUDE_CODE_OAUTH_TOKEN` with `CLAUDE_FORCE_OAUTH=1`. Never set or use
  `ANTHROPIC_API_KEY` in this spike. The API budget is $5–10 a month and is reserved.
- **Secrets.** Never print, echo, cat, log or write the token. Only test that it is set:
  `test -n "$CLAUDE_CODE_OAUTH_TOKEN" && echo set`. If it's missing, ask the user to run
  `claude setup-token` themselves and export it in their own shell or in `.data/spike/auth.env`
  (mode 600), then source that file without displaying it. Benchmark task images come from third-party
  repositories and receive this token, so suggest the user revokes it after the spike.
- **Pin versions.** Record `claude --version`, `harbor --version`, the git commit of this repo, model ids
  and the date for every run.
- Verify facts against `harbor run --help` and https://docs.harborframework.com/llms.txt rather than
  guessing flags or dataset names.

## Step 0: preflight

Confirm the environment before anything else:

- WSL2: `uname -r` contains `microsoft`, and the repo path is not under `/mnt/`. If it is, stop and ask
  the user to clone into the WSL filesystem.
- Line endings: `git ls-files --eol | grep -c 'w/crlf'` is 0.
- Docker: `docker info` works from Ubuntu. If it fails, ask the user to start Docker Desktop and enable
  WSL integration for this distro (Settings → Resources → WSL integration). Record server version, `NCPU`
  and `MemTotal` from `docker info`, which are the Docker Desktop VM's limits rather than the PC's.
- Disk: `docker system df` and `df -h` for the filesystem holding Docker's data.

Also record `uv --version` or `pipx --version`, `claude --version`, `git rev-parse HEAD`.
Stop and report if any check fails or resources are below the limits above.

## Step 1: install Harbor and smoke-test without a model

Install with `uv tool install harbor` (or pipx) inside Ubuntu, never on Windows. Run the oracle agent on
one small task from the Terminal-Bench sample dataset with `-n 1`. Record wall time and whether reward
was 1.

## Step 2: does the plugin load inside Harbor? (question 1)

Push-free check: the agent fetches this repo from GitHub at `BULEVO_REF`, so use a commit that exists on
`origin` (`git rev-parse origin/main`).

Run one trivial task with the probe plugin, Sonnet, k=1:

```bash
PYTHONPATH=. BULEVO_REF=<origin commit> BULEVO_PLUGIN=evals/spike/probe-plugin CLAUDE_FORCE_OAUTH=1 \
  harbor run -t <small task> -a evals.spike.bulevo_agent:BulevoClaudeCode -m anthropic/claude-sonnet-5 -n 1
```

In the job's agent logs find `claude-code.txt`: the first `system/init` event lists `plugins` and
`plugin_errors`. Also look for `bulevo-probe-session-start` under the trial's `sessions` directory
(proof the SessionStart hook ran). Record both. If `build_cli_flags` or the install hook fails, read
Harbor's installed `claude_code.py` and fix `evals/spike/bulevo_agent.py` minimally, then tell the user
what changed.

## Step 3: real cost and time (question 3)

Pick 2 tasks from the SWE-bench Pro dataset in Harbor whose repo is JS/TS (NodeBB, protonmail/webclients,
element-web or tutanota) and the smallest images you can identify. Run each with stock `-a claude-code`,
Sonnet, k=1, `-n 1`. Record image pull size and time, agent wall time, `total_cost_usd` (list-price
estimate under subscription), tokens, turns, reward. Do not run Opus unless the user confirms after
seeing Sonnet's numbers.

## Step 4: run-to-run variance hint (question 5)

Rerun one of the two tasks twice more (k=3 total). Record reward and cost spread. This is only a hint;
say so.

## Step 5: do agent questions reach a simulated user? (question 2)

Outside Harbor first, in a scratch directory under `.data/spike/`:

```bash
claude -p "Before doing anything, ask me which database I prefer using your question tool, then stop." \
  --output-format stream-json --verbose --model claude-sonnet-5 --max-turns 3
```

Record whether `AskUserQuestion` appears in the init tool list, whether it was called, and what result it
got in headless mode. Then read Harbor's "simulate a user" docs and report whether its ACP bridge would
deliver such a question; run it only if it looks cheap (one short task).

## Step 6: claude plugin eval under the subscription (question 4)

Needs Claude Code 2.1.269+ installed and logged in inside Ubuntu, plus `bubblewrap` and `socat` for the
sandbox (`sudo apt install bubblewrap socat`; ask the user to run the install, it needs their password).
From `evals/spike/probe-plugin`:

```bash
claude plugin eval . --trust-plugin --model claude-sonnet-5 --runs 2 --no-publish --json .data-eval.json
```

Move the JSON into `.data/spike/`. Record with/without scores, delta, cost estimate, any sandbox errors
(bubblewrap/socat) and whether auth worked.

## Step 7: report

Write `.data/spike/results.md` with a table: question, answer, evidence, numbers. Then summarize for the
user in Russian: what works, what doesn't, estimated cost per task per model, and a recommendation for
the eval system (Harbor for which contour, plugin eval for which). Estimate how many task runs per week
fit without hurting the user's normal Max usage, clearly marked as an estimate. List the Docker images the
spike pulled with their sizes, and offer the cleanup command (`docker image rm ...`) without running it.
