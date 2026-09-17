---
name: apply-retros
description: Turn new retros saved by /bulevo:retro on this machine into proposed harness fixes. Use when the user asks to process, review or apply retros.
disable-model-invocation: true
---

# Apply retros

Retros saved by `/bulevo:retro` describe real tasks where the harness helped or failed. Turn them into
changes to this repository. Speak in the language the user writes in.

## 1. Find new retros

For the plugin installed as `bulevo@bulevo-harness` the folder is
`~/.claude/plugins/data/bulevo-bulevo-harness/retros/` (under `$CLAUDE_CONFIG_DIR` instead of `~/.claude` if
that variable is set). If it's missing, look for any `~/.claude/plugins/data/*/retros` folder. Read every
retro whose frontmatter says `status: new`. If there are none, say so and stop.

## 2. Ground yourself

Read `docs/requirements.md` and the current files of every skill or agent the retros mention. Run
`git pull --ff-only` first if the working tree is clean, so fixes apply to the latest version.

## 3. Propose fixes

For each failure in the retros decide:

- **Harness or project.** Project-specific knowledge (a UI convention, a command, a module rule) belongs in
  that project's CLAUDE.md or skills, not in this repo. Tell the user what to add there.
- **The strongest fix that fits:** make it impossible (hook, tool restriction) › make it fail loudly with a
  fix hint › make it discoverable (skill instructions) › a sentence of prose.
- **Scope of the rule.** Write conditional rules ("for work from a design…") so one task doesn't bloat
  every task. A pattern seen once gets a narrow rule; widen it only when it repeats.
- **Whether it's already covered.** If an existing instruction was ignored, prefer making it more
  prominent or enforceable over adding a duplicate.

Present the proposals grouped by file, each with the retro evidence behind it, and ask which to apply.

## 4. Apply

Edit only the accepted proposals. Committed files are public: never copy project names, company terms,
code or personal data from retros into them; generalize. Show the diff and explain it. Commit and push only
when the user says so.

## 5. Close the loop

In each processed retro set `status: applied` or `status: rejected`, and add an `outcome:` line listing
the commit or the reason. These files stay local and are never committed.
