---
name: task
description: Turn a task into an agreed spec before any code is written. Understands intent, finds existing code, challenges the requirements, asks only what changes the code, and writes .claude/tasks/<slug>.md for approval.
argument-hint: "[task text, tracker text or file path]"
disable-model-invocation: true
---

# Task

The task: $ARGUMENTS

Your job in this skill is to understand the task and agree on what to build. **Write no application code
here.** Speak in the language the user writes in.

## 1. Read the settings

If `.claude/bulevo.json` exists in the directory the session started in, read `pushback` from it. The
default is `balanced`.

| Level | Questions | Counterproposals | Stop the task |
|---|---|---|---|
| `quiet` | Only for an explicit contradiction | None; note concerns in the spec | Never |
| `balanced` | Only when the answer changes the code | The single best alternative, with reasons | Risk to data, security, money or legal compliance |
| `strict` | Any ambiguity | Alternatives with cost and trade-offs | Also when the task likely won't solve the underlying problem |

## 2. Decide what kind of request this is

- **Investigate** ("why", "check", "figure out", "analyze", "разберись", "проверь почему"): answer with facts.
  Read code, run read-only commands, check logs or data, and cite the evidence. Don't edit files and don't
  write a spec. If the findings call for a change, offer to turn it into a task and stop.
- **Change**: continue below.
- **Unclear**: ask one question — investigate or change — and stop until answered.

If the whole change fits in one sentence, touches one or two places and leaves no decision open, say so
and ask whether to skip the spec and just do it.

## 3. Map the code

Delegate to the `bulevo:scout` subagent. Give it the task text and anything the user already said about
where the change lives. Read its report, then open the key files it names yourself before relying on them.

## 4. Analyze the requirements

Treat the requirements as a draft that may be wrong. Work through:

- **The problem behind the task.** Who needs this and why. Does the requested solution solve it?
- **Contradictions** with current behavior, existing code, data or other requirements.
- **Edge cases:** roles and permissions, empty and error states, concurrent edits, existing data and
  migrations, mobile and small screens for UI.
- **Side effects:** other features, services, reports or integrations the change affects.
- **A simpler or better approach**, reusing what the scout found first. Follow existing patterns by default;
  propose a fresh approach only as an explicit alternative with reasons.

Facts before hypotheses: when a conclusion depends on how the system behaves, check the code or data. Label
anything you could not verify as an assumption.

## 5. Ask and push back

Ask only questions whose answers lead to different code. Never ask what the code already answers. Use the
AskUserQuestion tool: at most 4 questions, 2–4 options each, recommended option first. If that tool isn't
available, ask in plain text and stop.

Present concerns and your alternative according to the pushback level. If a stop condition for the level is
met, explain the risk and wait for the user's decision instead of writing the spec.

## 6. Write the spec

Create `.claude/tasks/<YYYY-MM-DD>-<short-slug>.md` under the directory the session started in, in the
user's language:

```markdown
# <Task title>

## Problem
Who needs this and why, in two or three sentences.

## Decisions
Each question asked and the answer, and each alternative accepted or rejected with the reason.

## Scope
In scope / out of scope.

## Reuse
Existing code this change builds on, with path:line.

## Changes
Every place that changes, grouped by repository or layer, with path and what changes.

## Acceptance criteria
- [ ] Each one checkable by a command, a test, a query or a screenshot. No "works correctly".

## Verification
The exact commands and manual checks that prove the criteria, including UI screens to open.

## Risks and assumptions
What could go wrong, and what was assumed without verification.
```

## 7. Hand off

Show a short summary: the problem, key decisions, number of touch points, and the spec path. Ask the user
to approve or correct it. Stop there; implementation starts only after approval.
