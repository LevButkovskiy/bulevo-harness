[English](README.md) · [Русский](README.ru.md)

# bulevo-harness

A harness for [Claude Code](https://code.claude.com): plugins that make coding agents behave like careful
engineers — understand the problem, challenge the requirements, reuse what exists and prove their work — plus
the tooling to measure whether each change to the harness actually helps.

> **Status: early and experimental.** The plugin is at v0.1 and changes often. Expect rough edges.

## Install

In a Claude Code session:

```
/plugin marketplace add LevButkovskiy/bulevo-harness
/plugin install bulevo@bulevo-harness
```

Choose the **User** scope to use it in every project. To update later:

```
/plugin marketplace update bulevo-harness
```

## Use

### `/bulevo:task <task>`

Run it at the start of a task, before any code is written. It:

1. Tells investigating from changing. "Find out why…" gets an evidence-based answer and no edits.
2. Maps the codebase with a read-only `scout` subagent on a cheaper model: code to reuse, the pattern to
   follow and every place the change must touch.
3. Challenges the requirements: the problem behind the task, contradictions, edge cases, side effects and a
   simpler approach.
4. Asks only questions whose answers change the code.
5. Writes a spec to `.claude/tasks/<date>-<slug>.md` with verifiable acceptance criteria and stops for your
   approval.

Implement from the approved spec in a fresh session, for example: `Implement .claude/tasks/<file>.md`.

Works in a single repository and in a folder that contains several repositories.

### Settings

Optional `.claude/bulevo.json` in the project:

```json
{ "pushback": "balanced" }
```

| `pushback` | Behavior |
|---|---|
| `quiet` | Asks only on explicit contradictions; concerns go into the spec |
| `balanced` (default) | Asks when the answer changes the code; offers the best alternative; stops on risk to data, security, money or legal compliance |
| `strict` | Asks on any ambiguity; also stops when the task likely won't solve the underlying problem |

## Repository

| Path | What |
|---|---|
| `plugins/bulevo/` | The plugin |
| `docs/requirements.md` | What the harness must make agents do, and why |
| `tools/transcripts/` | Mine your own Claude Code transcripts for where agents needed correcting |
| `evals/` | Measuring harness changes; currently a spike with Harbor and `claude plugin eval` |

Contributors working on the harness with Claude Code: see [CLAUDE.md](CLAUDE.md).
