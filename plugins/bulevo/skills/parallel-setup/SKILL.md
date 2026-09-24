---
name: parallel-setup
description: Set up isolated parallel sessions in a workspace folder that holds several git repositories, where Claude Code's own worktrees don't work. Use when the user wants to run several tasks in parallel in such a workspace.
disable-model-invocation: true
---

# Parallel setup

Claude Code isolates parallel sessions with git worktrees, which needs the session folder to be a git
repository. A folder that only contains repositories gets no isolation, so parallel sessions would edit the
same files. This skill installs a WorktreeCreate/WorktreeRemove hook that builds an isolated copy of the
whole workspace for each session. Speak in the language the user writes in.

## 1. Check the workspace

The session folder must not be a git repository (`git rev-parse --git-dir` fails) and must contain at least
one folder with a `.git` entry. If it is a git repository, say that Claude Code's own `--worktree` already
works there and stop. List the repositories found. The folder's parent must not be inside a git repository
either, because the copies are created next to the workspace.

## 2. Install the script

Find a Python 3 that runs: `python3` on Linux and macOS, `py -3` on Windows. Copy
`${CLAUDE_PLUGIN_ROOT}/scripts/worktree.py` to `${CLAUDE_PLUGIN_DATA}/worktree.py`. The data folder keeps
the same path across plugin updates, so the hook doesn't break when the plugin updates; rerun this skill
after an update to refresh the copy.

## 3. Add the hooks

Show the user this block for `.claude/settings.local.json` in the workspace, with the real interpreter and
the absolute path of the copied script:

```json
{
  "hooks": {
    "WorktreeCreate": [{ "hooks": [{ "type": "command", "command": "<python> \"<data folder>/worktree.py\" create" }] }],
    "WorktreeRemove": [{ "hooks": [{ "type": "command", "command": "<python> \"<data folder>/worktree.py\" remove" }] }]
  }
}
```

Write it only after the user agrees. Merge it into the existing file and keep every other setting.

## 4. Explain how to use it

- The hook takes effect from the next session. A copy is for working on two tasks at once: ask
  `/bulevo:implement` for one, or run `claude --worktree <name>` from the workspace folder. A single task
  stays in the workspace, because the copy is where the code then sits and the user reads it. A copy lives
  in `<parent>/.<workspace>-worktrees/<name>/`: a git worktree of every repository on branch
  `worktree-<name>`, plus copies of the workspace's top-level files and `.claude` folder. Specs changed in
  the copy are synced back when it is removed.
- The branch starts from each repository's default branch. Set `BULEVO_WORKTREE_BASE=head` to start from the
  current checkout instead.
- `.env` files, or the patterns in a repository's `.worktreeinclude`, are copied. `node_modules` is linked
  from the main checkout where the system allows symlinks; otherwise dependencies need installing. Change
  the linked folders with `BULEVO_WORKTREE_LINK`.
- Parallel dev servers need different ports.
- On exit, Claude Code offers to remove the copy. Removal refuses while any repository has uncommitted
  changes; commits stay on the `worktree-<name>` branches.
- Whether the desktop app's worktree option uses this hook is untested; `claude --worktree` is verified.
