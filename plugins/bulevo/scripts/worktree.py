#!/usr/bin/env python3
"""WorktreeCreate / WorktreeRemove hook for a workspace folder that holds several git repositories.

Claude Code's default worktree isolation needs the session folder to be a git repository. A workspace
folder that only contains repositories gets none, so parallel sessions would edit the same files. This
hook builds an isolated copy of the workspace instead:

  <parent>/.<workspace>-worktrees/<name>/
    <repo>/          a git worktree of each repository, on branch worktree-<name>
    CLAUDE.md, ...   copies of the workspace's own top-level files and its .claude folder

Environment:
  BULEVO_WORKTREE_BASE   default (the repository's default branch, the default) or head (its current HEAD)
  BULEVO_WORKTREE_LINK   comma-separated folders to symlink from the main checkout, default node_modules

Configured by /bulevo:parallel-setup. Usage: worktree.py create|remove, with the hook JSON on stdin.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

MARKER = ".bulevo-worktree.json"
SKIP_TOP = {".claude", ".git", "node_modules"}


def log(msg):
    print(msg, file=sys.stderr)


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {repo}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_git_repo(path):
    return subprocess.run(["git", "-C", path, "rev-parse", "--git-dir"], capture_output=True).returncode == 0


def repos_in(workspace):
    return sorted(d for d in os.listdir(workspace)
                  if os.path.exists(os.path.join(workspace, d, ".git")))


def base_ref(repo):
    if os.environ.get("BULEVO_WORKTREE_BASE", "default") == "head":
        return "HEAD"
    ref = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False)
    return ref or "HEAD"


def copy_env_files(src, dst):
    include = os.path.join(src, ".worktreeinclude")
    if os.path.exists(include):
        with open(include, encoding="utf-8") as fh:
            patterns = [p.strip() for p in fh if p.strip() and not p.startswith("#")]
    else:
        patterns = [".env", ".env.*"]
    for pattern in patterns:
        for path in glob.glob(os.path.join(src, pattern), recursive=True):
            rel = os.path.relpath(path, src)
            target = os.path.join(dst, rel)
            if os.path.isfile(path) and not os.path.exists(target):
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(path, target)


def link_folders(src, dst):
    for name in filter(None, os.environ.get("BULEVO_WORKTREE_LINK", "node_modules").split(",")):
        source, target = os.path.join(src, name.strip()), os.path.join(dst, name.strip())
        if os.path.isdir(source) and not os.path.exists(target):
            try:
                os.symlink(source, target, target_is_directory=True)
            except OSError as exc:
                log(f"could not link {name} in {os.path.basename(dst)} ({exc}); install dependencies there")


def create(event):
    name = event["name"]
    workspace = os.path.realpath(event["cwd"])
    if is_git_repo(workspace):
        raise RuntimeError(f"{workspace} is a git repository; remove this hook to use Claude Code's own worktrees")
    repos = repos_in(workspace)
    if not repos:
        raise RuntimeError(f"no git repositories inside {workspace}")

    parent = os.path.dirname(workspace)
    root = os.path.join(parent, f".{os.path.basename(workspace)}-worktrees", name)
    if is_git_repo(parent):
        raise RuntimeError(f"{parent} is inside a git repository; worktrees must be created outside any repository")

    if not os.path.exists(os.path.join(root, MARKER)):
        os.makedirs(root, exist_ok=True)
        for entry in os.listdir(workspace):
            src = os.path.join(workspace, entry)
            if entry in repos or entry in SKIP_TOP or entry.startswith(".bulevo"):
                continue
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(root, entry))
        claude_dir = os.path.join(workspace, ".claude")
        if os.path.isdir(claude_dir):
            shutil.copytree(claude_dir, os.path.join(root, ".claude"), dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("worktrees"))

        branch = f"worktree-{name}"
        for repo in repos:
            src, dst = os.path.join(workspace, repo), os.path.join(root, repo)
            if git(src, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False):
                git(src, "worktree", "add", dst, branch)
            else:
                git(src, "worktree", "add", "-b", branch, dst, base_ref(src))
            copy_env_files(src, dst)
            link_folders(src, dst)
            log(f"{repo}: {branch}")

        with open(os.path.join(root, MARKER), "w", encoding="utf-8") as fh:
            json.dump({"workspace": workspace, "repos": repos, "branch": branch}, fh, indent=1)
    print(os.path.realpath(root))


def sync_tasks(root, workspace):
    """Specs are updated during implementation inside the copy; bring new or changed ones back."""
    src_dir = os.path.join(root, ".claude", "tasks")
    if not os.path.isdir(src_dir):
        return
    dst_dir = os.path.join(workspace, ".claude", "tasks")
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        src, dst = os.path.join(src_dir, name), os.path.join(dst_dir, name)
        if os.path.isfile(src) and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
            shutil.copy2(src, dst)
            log(f"spec synced back: {name}")


def remove(event):
    root = os.path.realpath(event["worktree_path"])
    marker = os.path.join(root, MARKER)
    if not os.path.exists(marker):
        raise RuntimeError(f"{root} was not created by this hook; not removing it")
    with open(marker, encoding="utf-8") as fh:
        info = json.load(fh)

    sync_tasks(root, info["workspace"])

    dirty = [r for r in info["repos"]
             if os.path.isdir(os.path.join(root, r)) and git(os.path.join(root, r), "status", "--porcelain")]
    if dirty:
        raise RuntimeError(f"uncommitted changes in {', '.join(dirty)}; commit or discard them first")

    for repo in info["repos"]:
        path = os.path.join(root, repo)
        if os.path.isdir(path):
            for name in os.listdir(path):
                if os.path.islink(os.path.join(path, name)):
                    os.unlink(os.path.join(path, name))  # never follow a link into the main checkout
            # only ignored files such as copied env files remain; commits stay on the branch
            git(os.path.join(info["workspace"], repo), "worktree", "remove", "--force", path)
    shutil.rmtree(root)
    log(f"removed {root}; branches {info['branch']} kept in each repository")


def main():
    handler = {"create": create, "remove": remove}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if handler is None:
        log("usage: worktree.py create|remove")
        sys.exit(2)
    try:
        handler(json.load(sys.stdin))
    except Exception as exc:
        log(f"bulevo worktree: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
