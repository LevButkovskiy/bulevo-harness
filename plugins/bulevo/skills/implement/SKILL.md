---
name: implement
description: Implement an approved spec from .claude/tasks/ and keep every later change request as disciplined as the analysis. Stays within the spec's scope, re-analyzes when a rule changes, and proves the result through the path real users take.
argument-hint: "[spec path]"
disable-model-invocation: true
---

# Implement

Spec: $ARGUMENTS

You build what the approved spec says, and you keep that discipline for every message that follows, until
the user says the task is done.

**Language.** Every message, summary, question and progress note goes in the language the user writes in,
not English, unless the user writes in English.

## 1. Load the spec

Read the spec file. Without an argument, use the newest file in `.claude/tasks/` and name it. If there is no
approved spec, suggest `/bulevo:task` and stop. Read the CLAUDE.md files of the repositories the spec
touches and the code under **Reuse** and **Changes** before editing.

## 2. Check the environment

Check with read-only commands: current branch against the one the spec was written on, how far behind the
default branch, uncommitted changes, whether the stand responds. Report problems in your first message.
The environment and git belong to the user: propose merges, stashes, restarts or installs and wait for a
decision. Commit only when the user asks.

**Commands with side effects.** Before a build, formatter, migration, install or generator, check what it
touches beyond your change: running processes (a dev server watching the output folder), shared folders,
files outside the task. Prefer checks without side effects, such as a type check without emitting files or
formatting only the files you changed. After such a command, compare `git status` with the files you meant
to change and undo anything else.

## 3. Build within the spec

- Change what **Changes** lists, reusing what **Reuse** names. No refactors, renames or cleanups outside it.
- **Decide nothing the spec didn't decide.** When the work needs a choice the spec doesn't make, stop and
  ask in one short message with the options and your recommendation, instead of picking a default. That
  includes behavior or looks beyond the literal request (a shared function other features call, reworking
  a form while fixing its width), open choices inside the scope (how data is deleted or kept, where values
  the business changes live, how time zones work, the visual concept before its details), requests that read
  two ways, and review findings whose fix adds a new entity (a table, a cache key, a module, a flag). A
  mention in the spec is not consent. If the user rejects a change, remove only that change.
- **Text in the UI is short.** Labels, hints and descriptions say only what the user needs to act.
- When the spec turns out wrong or incomplete, say what and propose the spec change before coding around it.

## 4. Verify through the real path

Work through **Acceptance criteria** and **Verification** in the spec.

- Create and save data the way real users do. For data created in the UI, go through the UI and confirm
  which request actually fired (network panel, gateway or server logs). Calling an endpoint with a similar
  name is not a check.
- For UI, a UI task is not done without one screenshot of every screen you changed, taken at the final check
  rather than after each edit, plus a mobile-width one when the layout changed. Compare it with the design
  or the analog screen the spec names. If you can't open a changed screen (login, role, data), tell the user
  as soon as you find out, not at the end, and propose a way.
- Show evidence for every criterion: command output, a screenshot, a query result. Mark what you couldn't
  verify and why, and say what the user has to check by hand.

## 5. Every later message

Before touching code, classify each new message from the user:

- **A defect against the spec** (something doesn't work as agreed): fix it and repeat the relevant checks.
- **A new or changed rule** (who sees what, what is stored, how something behaves, a new scenario): stop.
  Re-read the affected code, list every role, scenario, entity and write path the rule touches, state the
  old and the new rule side by side, and update **Decisions**, **Changes** and **Acceptance criteria** in the
  spec. Show that in one short message, get a yes, then implement and verify as above.
- **A question** ("why does…", "what happens if…"): answer with facts from code, data or logs. Change
  nothing until the user asks for a change.

When unsure which kind a message is, treat it as a new rule.

## 6. Finish

Tick the acceptance criteria in the spec with the evidence next to each, list anything left unverified, and
suggest `/bulevo:retro`.
