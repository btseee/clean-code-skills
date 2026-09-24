"""The shipped Claude Code hooks, run in a real shell the way the host runs them."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import support

SETTINGS = support.SKILL_ROOT / "assets" / "hooks" / "claude-settings.json"
BASH = shutil.which("bash")
# On Windows outside Git Bash, `bash` is the WSL launcher, which runs in another system.
POSIX_SHELL = BASH is not None and "system32" not in BASH.lower()


def hook_command(event: str) -> str:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return settings["hooks"][event][0]["hooks"][0]["command"]


@unittest.skipUnless(POSIX_SHELL, "needs a POSIX shell (Git Bash on Windows)")
class SessionStartHookTest(unittest.TestCase):
    def run_hook(self, files: dict) -> str:
        with tempfile.TemporaryDirectory() as directory:
            for path, text in files.items():
                target = Path(directory) / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            # HOME points inside the project, so no global install on this machine answers.
            completed = subprocess.run([BASH, "-c", hook_command("SessionStart")], cwd=directory,
                                       capture_output=True, text=True, timeout=60,
                                       env=dict(os.environ, HOME=directory))
        return completed.stdout

    def test_a_project_without_clean_hears_nothing(self):
        self.assertEqual(self.run_hook({"src/app.ts": "export {};\n"}), "")

    def test_packs_resolve_from_the_installed_skill(self):
        output = self.run_hook({
            ".clean/context.json": json.dumps({"packs": ["references/frameworks/react.md"]}),
            ".claude/skills/clean-code/references/frameworks/react.md": "# React\n",
        })
        self.assertIn("\n.claude/skills/clean-code/references/frameworks/react.md\n", output)
        self.assertIn("no declared layering", output)


if __name__ == "__main__":
    unittest.main()
