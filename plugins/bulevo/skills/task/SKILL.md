---
name: task
description: Turn a task into an agreed spec before any code is written. Understands intent, finds existing code, challenges the requirements, asks only what changes the code, and writes .claude/tasks/<slug>.md for approval.
argument-hint: "[task text, tracker text or file path]"
disable-model-invocation: true
---

# Task

The task: $ARGUMENTS

Your job in this skill is to understand the task and agree on what to build. **Write no application code
here.**

**Language.** Every message, summary, question and the spec itself go in the language the user writes in,
not English, unless the user writes in English.

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

If the request only records something (a note, a backlog or todo entry, a doc) and changes no application
code, do it now without asking: skip the scout, the environment check, the spec and approval. For choices
that are easy to change later, such as the file name or where it goes, follow existing files and name your
choice in the reply.

If a code change fits in one sentence, touches one or two places and leaves no decision open, say so and
ask whether to skip the spec and just do it.

If the task's headline promises more than its listed items (for example "match the design" followed by two
bullet points), ask whether to do only the listed items or everything the headline implies, and record the
answer in Scope.

## 3. Check the environment first

Before mapping the code, check with read-only commands what the analysis depends on: the current branch,
how far it is behind the default branch, uncommitted changes, whether the app or test stand responds,
whether dependencies look stale, and whether you can open and check every screen or endpoint the task will
change: login, the role it needs, test data, a working browser session. If you can't, that's a blocker:
say so now and propose a way (a test login, seed data, a dev-only sign-in) before any implementation, so
nothing gets built blind. If the branch diverges from the default branch or the tree is dirty, tell
the user in your next message and ask whether to switch or update before the analysis, because analysis on
the wrong branch has to be redone. Record the state in the spec. The environment and git belong to the
user: propose actions (merge, stash, start services, install dependencies) and wait for a decision; never do
them on your own.

## 3a. Map the code

Delegate to the `bulevo:scout` subagent. Give it the task text and anything the user already said about
where the change lives. Read its report, then open the key files it names yourself before relying on them.
Treat "doesn't exist" in the report as "not found under those names" until you've checked.

## 4. Analyze the requirements

Treat the requirements as a draft that may be wrong. Work through:

- **The problem behind the task.** Who needs this and why. Does the requested solution solve it?
- **Product constraints.** Check the requirements against what the project memory, CLAUDE.md and product docs
  say about positioning, audience, pricing and paid features, and quote what applies in **Decisions**. A
  limit or default that contradicts the product's direction is a wrong requirement.
- **Contradictions** with current behavior, existing code, data or other requirements.
- **Edge cases:** roles and permissions, empty and error states, concurrent edits, existing data and
  migrations, mobile and small screens for UI.
- **Access.** Roles named in a task describe who is affected, not how to check it. Build access rules on
  the mechanism the project already uses (for example privileges granted to roles) as the scout found it,
  never on role names from the task text. For anything whose display or saving depends on access, list
  what a user with different rights sees and saves when they open a record someone else created.
- **Side effects:** other features, services, reports or integrations the change affects.
- **A simpler or better approach**, reusing what the scout found first. Follow existing patterns by default;
  propose a fresh approach only as an explicit alternative with reasons.
- **UI without a design.** New or changed screens follow the closest existing screen of the same kind, as the
  scout describes it: container, header, button sizes and placement, how saving, creating and deleting
  work. Record it in **Follows pattern**; any deviation is a decision to ask about.
- **Work from a design** (Figma, mockup, screenshot): the task is about how it looks, not only what it does.
  For every affected element compare the design with the current app: font size, weight, line height,
  spacing, alignment, widths. Take design values from the design source and current values from computed
  styles. Compare the design frame size with the real container size in the app; a mismatch is a decision
  for the spec, not a risk. Derive sizes from the real container, including padding and icons inside
  controls, instead of copying percentages.

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
In scope, and an explicit list of what stays untouched.

## Environment
Branch state, stand, dependencies, and the actions proposed to the user before implementation.

## Follows pattern
Only for UI without a design: the analog screen and its layout, button sizes and placement, save, create
and delete flow that this change repeats.

## Design fidelity
Only for work from a design: one row per element and property — design value, current value, decision.
Include the design frame size against the real container size.

## Reuse
Existing code this change builds on, with path:line.

## Changes
Every place that changes, grouped by repository or layer, with path and what changes.

## Acceptance criteria
- [ ] Each one checkable by a command, a test, a query or a screenshot. No "works correctly".

## Verification
The exact commands and manual checks that prove the criteria. Run each command before writing it here, or
mark it (unverified). Make sure each check can pass in the real environment: when data changes on its own
(background jobs, live traffic), compare old and new behavior on the same snapshot rather than at different
times; when a table is empty, an index or plan criterion needs data; when a dev server is running, a build
that cleans its output folder breaks it. When a criterion needs another role, account or data state, say how to get it, or mark
it as a manual check for the user. For UI: a screenshot next to the design at the same scale, checked by
eye for alignment and baselines; DOM measurements alone don't count.

## Risks and assumptions
What could go wrong, and what was assumed without verification.
```

## 7. Hand off

Show a short summary: the problem, key decisions, number of touch points, and the spec path. Ask the user
to approve or correct it. Stop there; implementation starts only after approval, with
`/bulevo:implement <spec path>`, preferably in a fresh session: a long session re-reads its whole history on
every turn.
