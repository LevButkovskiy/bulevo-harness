---
name: apply-retros
description: Turn new retros saved by /bulevo:retro on this machine into proposed harness fixes, by root cause rather than by symptom. Use when the user asks to process, review or apply retros.
disable-model-invocation: true
---

# Apply retros

Retros saved by `/bulevo:retro` describe real tasks where the harness helped or failed. Turn them into
changes to this repository without letting the skills grow into a list of special cases. Speak in the
language the user writes in.

## 1. Read the retros

For the plugin installed as `bulevo@bulevo-harness` the folder is
`~/.claude/plugins/data/bulevo-bulevo-harness/retros/` (under `$CLAUDE_CONFIG_DIR` instead of `~/.claude` if
that variable is set). If it's missing, look for any `~/.claude/plugins/data/*/retros` folder. Process the
retros with `status: new`. Read the earlier ones too: they are the history that shows what repeats. If
there are no new retros, say so and stop.

## 2. Ground yourself

Run `git pull --ff-only` first if the working tree is clean. Read `docs/requirements.md` and the current
files of every skill or agent the retros mention.

## 3. Find root causes

Retros list symptoms: a misaligned button, a wrong time zone, an unasked delete policy. Group every
correction across all retros by the cause behind it, such as "chose a default the spec didn't decide" or
"handed over UI without looking at it". Check which version of the plugin and which skills the task
actually ran through: a failure in a step that ran outside the skill says nothing about the skill.

For each cause decide:

- **Harness or project.** Knowledge about one project belongs to that project, and the agent working there
  records it. Don't propose what the project should add.
- **Repeated or not.** Change the harness only for a cause seen in at least two tasks. Record a cause seen
  once as an observation in the retro's `outcome:` so a later run can find the repeat.
- **Already covered.** If an existing instruction was ignored, prefer making it more prominent or
  enforceable over adding another.
- **The strongest fix that fits:** make it impossible (hook, tool restriction) › make it fail loudly with a
  fix hint › make it discoverable (skill instructions) › a sentence of prose.
- **General, not specific.** One rule that names the cause and gives the symptoms as examples beats a rule
  per symptom. A skill must not grow with every retro: when you add a rule, look for one to merge or remove,
  and propose deleting rules that no task has needed.

Present the causes, the evidence from each retro, and the proposed change, and ask which to apply.

## 4. Apply

Edit only the accepted proposals. Committed files are public: never copy project names, company terms,
code or personal data from retros into them; generalize. Show the diff and explain it. Commit and push only
when the user says so.

## 5. Close the loop

In each processed retro set `status: applied`, `status: observed` (a cause recorded, no change yet) or
`status: rejected`, and add an `outcome:` line with the commit, the observed causes or the reason. These
files stay local and are never committed.
