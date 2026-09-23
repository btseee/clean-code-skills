#!/usr/bin/env python3
"""Grade an eval run: did the agent's changes meet the case's checkable expectations?

Each case under evals/cases/<id>/ has a case.json (prompt and expectations) and a
repo/ fixture. An agent works on a copy of the fixture; this script compares the
finished copy with the expectations and writes a grading.json in the shape
skill-creator aggregates: expectations with text, passed, and evidence, plus a
summary. An expectation that needs a transcript, when none is given, is skipped
(passed: null), never guessed.

Usage:
    python evals/grade.py --case evals/cases/<id> --workspace <finished copy>
                          [--transcript <file>] [--output grading.json]
    python evals/grade.py --self-test               # every case is well-formed and not vacuous
    python evals/grade.py --export-evals evals/evals.json

Standard library only. Repository-only: the installer never copies evals/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
CASES_DIR = EVALS_DIR / "cases"
REPO_ROOT = EVALS_DIR.parent
SKILL_ROOT = REPO_ROOT / "skills" / "clean-code"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import project_files  # noqa: E402  (the skill's scripts folder, put on the path above)

REQUIRED_FIELDS = {
    "file_exists": ("glob",),
    "file_contains": ("glob", "pattern"),
    "file_not_contains": ("glob", "pattern"),
    "unchanged": ("path",),
    "no_new_files": ("glob",),
    "map_finding_absent": ("kind",),
    "boundaries_pass": (),
    "transcript_reads": ("pattern",),
}
CASE_KEYS = ("id", "pack", "prompt", "expected_output", "expectations")
SKIPPED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "vendor", "dist", "build"}
MAP_FINDING_KINDS = {"misplaced", "mixed", "duplicates", "name_clashes", "synonyms", "cycles"}


def files_in(root: Path) -> list:
    """Every file under root, dot-folders such as .clean included."""
    found = []
    for current, folders, names in os.walk(root):
        folders[:] = sorted(folder for folder in folders if folder not in SKIPPED_DIRS)
        for name in sorted(names):
            found.append((Path(current) / name).relative_to(root).as_posix())
    return found


def _read(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            return handle.read().replace("\r\n", "\n").replace("\r", "\n")
    except OSError:
        return ""


def _matching(workspace: Path, glob: str) -> list:
    return [path for path in files_in(workspace) if project_files.glob_match(glob, path)]


def _search(workspace: Path, paths, pattern: str):
    regex = re.compile(pattern, re.M)
    for path in paths:
        text = _read(workspace / path)
        match = regex.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            return f"{path}:{line}: {text.splitlines()[line - 1].strip()[:120]}"
    return None


def check(expectation: dict, fixture: Path, workspace: Path, transcript):
    """(passed, evidence) for one expectation; passed is None when it cannot be judged."""
    kind = expectation["type"]
    if kind == "file_exists":
        matches = _matching(workspace, expectation["glob"])
        return bool(matches), ", ".join(matches[:5]) or f"no file matches {expectation['glob']}"
    if kind in {"file_contains", "file_not_contains"}:
        matches = _matching(workspace, expectation["glob"])
        hit = _search(workspace, matches, expectation["pattern"])
        if kind == "file_contains":
            return hit is not None, hit or f"no match in {len(matches)} file(s)"
        return hit is None, hit or f"no match in {len(matches)} file(s)"
    if kind == "unchanged":
        path = expectation["path"]
        if not (workspace / path).is_file():
            return False, f"{path} is missing"
        same = _read(workspace / path) == _read(fixture / path)
        return same, f"{path} {'is unchanged' if same else 'was changed'}"
    if kind == "no_new_files":
        before = set(files_in(fixture))
        new = [path for path in _matching(workspace, expectation["glob"]) if path not in before]
        return not new, ", ".join(new[:5]) or "no new matching files"
    if kind == "map_finding_absent":
        return _map_finding_absent(workspace, expectation)
    if kind == "boundaries_pass":
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_boundaries.py"), "--root", str(workspace)],
            capture_output=True, text=True, timeout=120)
        tail = (completed.stdout.strip().splitlines() or ["(no output)"])[-1]
        return completed.returncode == 0, f"exit {completed.returncode}: {tail.strip()}"
    if kind == "transcript_reads":
        if transcript is None:
            return None, "no transcript supplied"
        hit = re.search(expectation["pattern"], _read(Path(transcript)))
        return bool(hit), hit.group(0) if hit else "not read"
    raise ValueError(f"unknown expectation type {kind!r}")


def _map_finding_absent(workspace: Path, expectation: dict):
    import map_structure
    data = map_structure.build_map(workspace, map_structure.packs_for(workspace, None), 2)
    prefix = expectation.get("path")
    items = data["findings"][expectation["kind"]]
    if prefix:
        items = [item for item in items if json.dumps(item).find(prefix) >= 0]
    return not items, f"{len(items)} {expectation['kind']} finding(s)"


def grade(case_dir: Path, workspace: Path, transcript=None) -> dict:
    case = json.loads((Path(case_dir) / "case.json").read_text(encoding="utf-8"))
    fixture = Path(case_dir) / "repo"
    results = []
    for expectation in case["expectations"]:
        passed, evidence = check(expectation, fixture, Path(workspace), transcript)
        results.append({"text": expectation["text"], "passed": passed, "evidence": evidence})
    judged = [result for result in results if result["passed"] is not None]
    passed_count = sum(1 for result in judged if result["passed"])
    return {
        "case": case["id"],
        "expectations": results,
        "summary": {
            "passed": passed_count,
            "failed": len(judged) - passed_count,
            "skipped": len(results) - len(judged),
            "total": len(results),
            "pass_rate": round(passed_count / len(judged), 3) if judged else None,
        },
    }


def _case_problems(case_dir: Path) -> list:
    where = case_dir.name
    try:
        case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"{where}: case.json unreadable: {error}"]
    problems = [f"{where}: missing key {key!r}" for key in CASE_KEYS if key not in case]
    if problems:
        return problems
    if case["id"] != where:
        problems.append(f"{where}: id {case['id']!r} differs from its folder")
    if case["pack"] != "core" and not (SKILL_ROOT / "references" / case["pack"]).is_file():
        problems.append(f"{where}: pack {case['pack']!r} does not exist")
    fixture = case_dir / "repo"
    if not fixture.is_dir() or not files_in(fixture):
        problems.append(f"{where}: repo/ fixture is missing or empty")
        return problems
    if not case["expectations"]:
        problems.append(f"{where}: no expectations")
    for index, expectation in enumerate(case["expectations"]):
        label = f"{where}: expectation {index + 1}"
        kind = expectation.get("type")
        if kind not in REQUIRED_FIELDS:
            problems.append(f"{label}: unknown expectation type {kind!r}")
            continue
        missing = [field for field in REQUIRED_FIELDS[kind] + ("text",) if not expectation.get(field)]
        problems += [f"{label}: missing {field!r}" for field in missing]
        if expectation.get("pattern"):
            try:
                re.compile(expectation["pattern"])
            except re.error as error:
                problems.append(f"{label}: invalid pattern: {error}")
        if kind == "unchanged" and not (fixture / expectation.get("path", "")).is_file():
            problems.append(f"{label}: {expectation.get('path')!r} is not in the fixture")
        if kind == "map_finding_absent" and expectation.get("kind") not in MAP_FINDING_KINDS:
            problems.append(f"{label}: unknown finding kind {expectation.get('kind')!r}")
    if problems:
        return problems
    untouched = grade(case_dir, fixture)
    if not any(result["passed"] is False for result in untouched["expectations"]):
        problems.append(f"{where}: every expectation passes on its untouched fixture, "
                        "so the case tests nothing")
    return problems


def check_cases(cases_dir: Path) -> list:
    """Problems with every case under cases_dir; [] when all are well-formed."""
    problems = []
    for case_dir in sorted(path for path in Path(cases_dir).iterdir() if path.is_dir()):
        problems += _case_problems(case_dir)
    return problems


def export_evals(cases_dir: Path = CASES_DIR) -> dict:
    """The cases in skill-creator's evals.json shape."""
    evals = []
    for number, case_dir in enumerate(sorted(path for path in cases_dir.iterdir() if path.is_dir()), 1):
        case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        evals.append({
            "id": number,
            "name": case["id"],
            "prompt": case["prompt"],
            "expected_output": case["expected_output"],
            "files": [f"evals/cases/{case['id']}/repo"],
            "expectations": [expectation["text"] for expectation in case["expectations"]],
        })
    return {"skill_name": "clean-code", "evals": evals}


def _write_lf(path: Path, text: str) -> None:
    """Write with LF endings on every platform: the file may be committed."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grade clean-code eval runs.")
    parser.add_argument("--case", help="case folder, evals/cases/<id>")
    parser.add_argument("--workspace", help="the agent's finished copy of the fixture")
    parser.add_argument("--transcript", help="the run's transcript, for transcript_reads")
    parser.add_argument("--output", help="write grading JSON here instead of stdout")
    parser.add_argument("--self-test", action="store_true", help="check every case")
    parser.add_argument("--export-evals", metavar="PATH", help="write skill-creator evals.json")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])
    if arguments.self_test:
        problems = check_cases(CASES_DIR)
        exported = EVALS_DIR / "evals.json"
        if exported.is_file() and json.loads(exported.read_text(encoding="utf-8")) != export_evals():
            problems.append("evals/evals.json is stale: run grade.py --export-evals evals/evals.json")
        for problem in problems:
            print(f"FAIL: {problem}")
        count = sum(1 for path in CASES_DIR.iterdir() if path.is_dir())
        print(f"{count} case(s) checked, {len(problems)} problem(s)")
        return 1 if problems else 0
    if arguments.export_evals:
        _write_lf(Path(arguments.export_evals), json.dumps(export_evals(), indent=2) + "\n")
        return 0
    if not (arguments.case and arguments.workspace):
        print("error: --case and --workspace are required (or use --self-test)", file=sys.stderr)
        return 2
    result = json.dumps(grade(Path(arguments.case), Path(arguments.workspace), arguments.transcript),
                        indent=2)
    if arguments.output:
        _write_lf(Path(arguments.output), result + "\n")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
