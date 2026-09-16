"""Harbor agent: stock Claude Code plus a plugin from the public bulevo-harness repo.

Harbor's built-in `claude-code` agent has no plugin option, so this subclass downloads
the repo at a pinned ref inside the task container and adds `--plugin-dir`.

    PYTHONPATH=. BULEVO_REF=<commit> BULEVO_PLUGIN=evals/spike/probe-plugin \
      harbor run -t <task> -a evals.spike.bulevo_agent:BulevoClaudeCode -m anthropic/<model>

The harness-off arm of a comparison is the stock `-a claude-code` on the same tasks.
"""
import os
import shlex

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.environments.base import BaseEnvironment

REPO_TARBALL = "https://codeload.github.com/LevButkovskiy/bulevo-harness/tar.gz/{ref}"
REMOTE_ROOT = "/opt/bulevo-harness"


class BulevoClaudeCode(ClaudeCode):
    @staticmethod
    def name() -> str:
        return "bulevo-claude-code"

    def _plugin_path(self) -> str:
        plugin = os.environ.get("BULEVO_PLUGIN", "").strip("/")
        if not plugin:
            raise RuntimeError("Set BULEVO_PLUGIN to the plugin path inside the repo, e.g. evals/spike/probe-plugin")
        return f"{REMOTE_ROOT}/{plugin}"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        ref = os.environ.get("BULEVO_REF", "main")
        url = shlex.quote(REPO_TARBALL.format(ref=ref))
        # --strip-components drops the "bulevo-harness-<ref>/" top directory of the GitHub tarball
        fetch = (
            f"mkdir -p {REMOTE_ROOT} && "
            f"(curl -fsSL {url} || wget -qO- {url} || "
            f"python3 -c \"import sys,urllib.request;sys.stdout.buffer.write(urllib.request.urlopen({url}).read())\") "
            f"| tar -xz --strip-components=1 -C {REMOTE_ROOT} && "
            f"test -f {shlex.quote(self._plugin_path())}/.claude-plugin/plugin.json && "
            f"chmod -R a+rX {REMOTE_ROOT}"
        )
        await self.exec_as_root(environment, command=fetch)

    def build_cli_flags(self) -> str:
        base = super().build_cli_flags() or ""
        return f"{base} --plugin-dir {shlex.quote(self._plugin_path())}".strip()
