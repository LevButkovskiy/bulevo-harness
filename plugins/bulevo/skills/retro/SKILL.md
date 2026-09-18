---
name: retro
description: Retrospective of a finished task. Collects the facts from this session's transcript, asks the user five short questions, and saves a plain-text retro that the harness maintainers turn into fixes. Use at the end of a task.
argument-hint: "[spec path or extra session ids]"
disable-model-invocation: true
---

# Retro

Extra input: $ARGUMENTS

Look back at the task just finished and record what the harness should learn from it. Change no project
files.

**Language.** Every message, question and the retro itself go in the language the user writes in, not
English, unless the user writes in English.

## 1. Collect the facts

Run the bundled script with `python3`, or `python` if `python3` isn't available:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcripts.py" --session ${CLAUDE_SESSION_ID} --mentions <spec-file-name> --since-hours 72
```

Pass `--mentions` with the spec's file name when the task has a spec in `.claude/tasks/` (from the arguments
or the conversation), so a separate implementation session is included. Add `--session <id>` for any session
ids in the arguments. The output has one metrics line and one dialogue digest per session.

From it and the conversation, work out:

- how each `/bulevo:task` step went, if it ran: request type, whether the scout ran and on which model, the
  questions asked, the spec
- every correction the user made: what they said, at which stage (spec or implementation), and the category
  (wrong approach, overengineering, incomplete, didn't verify, standards or style, misunderstood the task,
  ignored an instruction, environment)
- what in the spec held up during implementation, what turned out wrong, and what it missed
- numbers: prompts, tool calls, time, tokens by model, and which phases took the most

## 2. Ask the user

Use AskUserQuestion, two calls of at most four questions each, each with 2–4 short options; the user adds
detail through "Other". Ask about:

1. Understanding of the task: accurate / partly / missed the point
2. Questions to the user: useful / none needed / missing ones / too many
3. Existing code and touch points: all found / missed some / wrong
4. Spec against reality: held up / gaps / wrong
5. Where they corrected the agent: nowhere / spec / implementation / both

Then ask in plain text whether anything else surprised them, and wait for the answer. If AskUserQuestion
isn't available, ask the five questions in one plain-text message.

## 3. Write the retro

Plain prose paragraphs, no tables: the user copies and reads it in places where tables break. No code
snippets, no secrets, no personal data. Sections:

- **Task:** one sentence, and which sessions it spanned
- **How the skills went:** step by step
- **Corrections:** each with the user's point, stage and category
- **Spec against reality:** held up, wrong, missed
- **User's assessment:** the five answers and the free comment
- **Numbers:** time, prompts, tool calls, tokens by model, the most expensive phases
- **Proposed harness fixes:** for each correction, the smallest change that would have prevented it and
  where it belongs (task skill, scout, a new skill, a hook, the project's own CLAUDE.md or skills). Say when
  a failure belongs to the project rather than the harness.

## 4. Save it

Write the retro to `${CLAUDE_PLUGIN_DATA}/retros/<YYYY-MM-DD>-<project>-<short-slug>.md`, starting with:

```
---
status: new
date: <YYYY-MM-DD>
project: <project folder name>
sessions: [<session ids>]
---
```

Tell the user the saved path and give a three-sentence summary. The harness maintainers pick up new retros
from this folder on this machine.
