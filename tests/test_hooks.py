"""The shipped Claude Code hooks, run in a real shell the way the host runs them."""

import json
import os
import shutil
import subprocess
import sys
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


def write_files(root: Path, files: dict) -> None:
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        if path.startswith("bin/"):
            target.chmod(0o755)


def run_hook(event: str, root: Path) -> str:
    """The hook's output in a project at root, whose bin/ comes first on PATH."""
    # HOME points inside the project, so no global install on this machine answers.
    environment = dict(os.environ, HOME=str(root),
                       PATH=str(root / "bin") + os.pathsep + os.environ.get("PATH", ""))
    completed = subprocess.run([BASH, "-c", hook_command(event)], cwd=root, capture_output=True,
                               text=True, timeout=120, env=environment)
    return completed.stdout


# `python3` found on PATH that cannot run, as the Microsoft Store stub on Windows; `python`
# runs the interpreter running these tests.
BROKEN_PYTHON3 = {
    "bin/python3": "#!/bin/sh\nexit 9009\n",
    "bin/python": '#!/bin/sh\nexec "%s" "$@"\n' % Path(sys.executable).as_posix(),
}


@unittest.skipUnless(POSIX_SHELL, "needs a POSIX shell (Git Bash on Windows)")
class SessionStartHookTest(unittest.TestCase):
    def run_hook(self, files: dict) -> str:
        with tempfile.TemporaryDirectory() as directory:
            write_files(Path(directory), files)
            return run_hook("SessionStart", Path(directory))

    def test_a_project_without_clean_hears_nothing(self):
        self.assertEqual(self.run_hook({"src/app.ts": "export {};\n"}), "")

    def test_packs_resolve_from_the_installed_skill(self):
        output = self.run_hook({
            ".clean/context.json": json.dumps({"packs": ["references/frameworks/react.md"]}),
            ".claude/skills/clean-code/references/frameworks/react.md": "# React\n",
        })
        self.assertIn("\n.claude/skills/clean-code/references/frameworks/react.md\n", output)
        self.assertIn("no declared layering", output)

    def test_a_python_that_cannot_run_is_passed_over(self):
        output = self.run_hook(dict(BROKEN_PYTHON3, **{
            ".clean/context.json": json.dumps({"packs": ["references/languages/python.md"]}),
            ".claude/skills/clean-code/references/languages/python.md": "# Python\n",
        }))
        self.assertIn("\n.claude/skills/clean-code/references/languages/python.md\n", output)

    def test_a_pack_scoped_to_other_projects_shows_its_folders(self):
        output = self.run_hook({
            ".clean/context.json": json.dumps({
                "packs": ["references/languages/typescript.md", "references/frameworks/react.md"],
                "pack_scopes": {"references/frameworks/react.md": ["web", "admin"]},
            }),
            ".claude/skills/clean-code/references/frameworks/react.md": "# React\n",
        })
        self.assertIn("\n.claude/skills/clean-code/references/languages/typescript.md\n", output)
        self.assertIn("\n.claude/skills/clean-code/references/frameworks/react.md (web/, admin/)\n", output)


@unittest.skipUnless(POSIX_SHELL, "needs a POSIX shell (Git Bash on Windows)")
class PostToolUseHookTest(unittest.TestCase):
    def test_the_boundary_check_runs_when_python3_cannot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(support.SCRIPTS_DIR, root / ".claude/skills/clean-code/scripts",
                            ignore=shutil.ignore_patterns("__pycache__"))
            write_files(root, dict(BROKEN_PYTHON3, **{
                ".clean/architecture.md": "```clean-architecture\nlayer domain = src/domain/**\n"
                                          "layer infra = src/infra/**\n```\n",
                "src/domain/order.ts": "import { Db } from '../infra/db';\n",
                "src/infra/db.ts": "export const Db = 1;\n",
            }))
            output = run_hook("PostToolUse", root)
        self.assertIn("src/domain/order.ts:1: domain -> infra", output)


if __name__ == "__main__":
    unittest.main()
