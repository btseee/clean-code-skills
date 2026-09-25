import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import support

sys.path.insert(0, str(support.REPO_ROOT / "evals"))
import grade  # noqa: E402  (lives in evals/, put on the path above)


def write(root: Path, files: dict) -> None:
    """Write files byte for byte: text mode on Windows would rewrite the line endings."""
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.case = base / "cases" / "demo"
        self.workspace = base / "workspace"
        write(self.case / "repo", {
            "src/services/pay.js": "function pay() {}\r\nmodule.exports = { pay };\r\n",
            "src/app.js": "const pay = require('./services/pay');\n",
        })
        shutil.copytree(self.case / "repo", self.workspace)

    def tearDown(self):
        self.directory.cleanup()

    def grade_one(self, expectation, transcript=None):
        case = {"id": "demo", "pack": "core", "prompt": "p", "expected_output": "e",
                "expectations": [dict(expectation, text="t")]}
        (self.case / "case.json").write_text(json.dumps(case), encoding="utf-8")
        result = grade.grade(self.case, self.workspace, transcript)
        return result["expectations"][0]["passed"]

    def write_transcript(self, calls) -> Path:
        """A JSON-lines transcript of (tool name, input dict) tool_use calls, in order."""
        path = self.workspace.parent / "transcript.jsonl"
        records = [{"type": "assistant", "message": {"content": [
                   {"type": "tool_use", "name": name, "input": tool_input}]}}
                  for name, tool_input in calls]
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
        return path

    def test_file_exists_and_contains(self):
        self.assertFalse(self.grade_one({"type": "file_exists", "glob": "src/middleware/*.js"}))
        write(self.workspace, {"src/middleware/limit.js": "module.exports = (req, res, next) => next();\n"})
        self.assertTrue(self.grade_one({"type": "file_exists", "glob": "src/middleware/*.js"}))
        self.assertTrue(self.grade_one({"type": "file_contains", "glob": "src/middleware/*.js",
                                        "pattern": r"req, res, next"}))
        self.assertFalse(self.grade_one({"type": "file_not_contains", "glob": "src/**",
                                         "pattern": r"next\(\)"}))

    def test_unchanged_ignores_line_endings_but_not_edits(self):
        (self.workspace / "src/services/pay.js").write_text(
            "function pay() {}\nmodule.exports = { pay };\n", encoding="utf-8")
        self.assertTrue(self.grade_one({"type": "unchanged", "path": "src/services/pay.js"}))
        (self.workspace / "src/services/pay.js").write_text("function pay() { throw 1; }\n",
                                                          encoding="utf-8")
        self.assertFalse(self.grade_one({"type": "unchanged", "path": "src/services/pay.js"}))

    def test_no_new_files_flags_sibling_variants(self):
        self.assertTrue(self.grade_one({"type": "no_new_files", "glob": "**/*_v2.*"}))
        write(self.workspace, {"src/services/pay_v2.js": "function pay() {}\n"})
        self.assertFalse(self.grade_one({"type": "no_new_files", "glob": "**/*_v2.*"}))

    def test_no_new_files_ignores_what_installing_a_dependency_writes(self):
        write(self.workspace, {"package-lock.json": "{}\n", ".gitignore": "node_modules/\n"})
        self.assertTrue(self.grade_one({"type": "no_new_files", "glob": "*"}))
        write(self.workspace, {"debug.log": "trace\n"})
        self.assertFalse(self.grade_one({"type": "no_new_files", "glob": "*"}))

    def test_new_file_is_the_inverse_of_no_new_files(self):
        self.assertFalse(self.grade_one({"type": "new_file", "glob": "**/*.test.*"}))
        write(self.workspace, {"src/services/pay.test.js": "test('pays', () => {});\n"})
        self.assertTrue(self.grade_one({"type": "new_file", "glob": "**/*.test.*"}))

    def test_new_file_accepts_any_of_several_globs(self):
        expectation = {"type": "new_file", "glob": ["**/*.test.js", "test/**"]}
        self.assertFalse(self.grade_one(expectation))
        write(self.workspace, {"test/checkout.js": "test('totals', () => {});\n"})
        self.assertTrue(self.grade_one(expectation))

    def test_new_file_ignores_what_installing_a_dependency_writes(self):
        write(self.workspace, {"package-lock.json": "{}\n", ".gitignore": "node_modules/\n"})
        self.assertFalse(self.grade_one({"type": "new_file", "glob": "*"}))
        write(self.workspace, {"debug.log": "trace\n"})
        self.assertTrue(self.grade_one({"type": "new_file", "glob": "*"}))

    def test_transcript_reads_is_skipped_without_a_transcript(self):
        expectation = {"type": "transcript_reads", "pattern": r"frameworks/express\.md"}
        self.assertIsNone(self.grade_one(expectation))
        transcript = self.workspace.parent / "transcript.txt"
        transcript.write_text("Read skills/clean-code/references/frameworks/express.md\n",
                              encoding="utf-8")
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_transcript_reads_matches_windows_paths_in_a_json_transcript(self):
        expectation = {"type": "transcript_reads", "pattern": r"frameworks/express\.md"}
        transcript = self.workspace.parent / "transcript.jsonl"
        transcript.write_bytes(
            b'{"input": {"file_path": "D:\\\\skills\\\\references\\\\frameworks\\\\express.md"}}\n')
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_transcript_reads_counts_tool_calls_not_text_the_run_was_shown(self):
        expectation = {"type": "transcript_reads", "pattern": r"frameworks/express\.md"}
        transcript = self.workspace.parent / "run.jsonl"
        shown = {"type": "user", "message": {"content": [{"type": "tool_result", "content":
                 '{"packs": ["references/frameworks/express.md"]}'}]}}
        transcript.write_text(json.dumps(shown) + "\n", encoding="utf-8")
        self.assertFalse(self.grade_one(expectation, transcript))
        read = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read",
                "input": {"file_path": "D:\\skill\\references\\frameworks\\express.md"}}]}}
        transcript.write_text(json.dumps(shown) + "\n" + json.dumps(read) + "\n", encoding="utf-8")
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_read_before_edit_is_skipped_without_a_transcript(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        self.assertIsNone(self.grade_one(expectation))

    def test_read_before_edit_passes_when_the_matching_read_comes_first(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        transcript = self.write_transcript([
            ("Read", {"file_path": "skills/clean-code/references/frameworks/express.md"}),
            ("Edit", {"file_path": "src/app.js", "old_string": "a", "new_string": "b"}),
        ])
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_read_before_edit_fails_when_the_edit_comes_first(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        transcript = self.write_transcript([
            ("Edit", {"file_path": "src/app.js", "old_string": "a", "new_string": "b"}),
            ("Read", {"file_path": "skills/clean-code/references/frameworks/express.md"}),
        ])
        self.assertFalse(self.grade_one(expectation, transcript))

    def test_read_before_edit_fails_when_never_read(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        transcript = self.write_transcript([("Write", {"file_path": "src/new.js", "content": "x"})])
        self.assertFalse(self.grade_one(expectation, transcript))

    def test_read_before_edit_passes_with_no_file_changing_call_at_all(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        transcript = self.write_transcript([
            ("Read", {"file_path": "skills/clean-code/references/frameworks/express.md"}),
            ("Grep", {"pattern": "TODO"}),
        ])
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_read_before_edit_matches_windows_paths(self):
        expectation = {"type": "read_before_edit", "pattern": r"frameworks/express\.md"}
        transcript = self.write_transcript([
            ("Read", {"file_path": "D:\\skill\\references\\frameworks\\express.md"}),
            ("Edit", {"file_path": "src/app.js"}),
        ])
        self.assertTrue(self.grade_one(expectation, transcript))

    def test_command_passes_on_exit_zero(self):
        expectation = {"type": "command_passes", "timeout": 10,
                       "command": [sys.executable, "-c", "pass"]}
        self.assertTrue(self.grade_one(expectation))

    def test_command_passes_fails_with_the_tail_of_the_output(self):
        case = {"id": "demo", "pack": "core", "prompt": "p", "expected_output": "e", "expectations": [
            {"type": "command_passes", "text": "t", "timeout": 10,
             "command": [sys.executable, "-c", "import sys; print('boom'); sys.exit(1)"]},
        ]}
        (self.case / "case.json").write_text(json.dumps(case), encoding="utf-8")
        result = grade.grade(self.case, self.workspace, None)["expectations"][0]
        self.assertFalse(result["passed"])
        self.assertIn("boom", result["evidence"])

    def test_command_passes_is_skipped_when_the_executable_is_missing(self):
        expectation = {"type": "command_passes", "timeout": 5,
                       "command": ["definitely-not-a-real-executable-xyz123"]}
        self.assertIsNone(self.grade_one(expectation))

    def test_command_passes_runs_with_the_workspace_as_cwd(self):
        write(self.workspace, {"marker.txt": "present\n"})
        expectation = {"type": "command_passes", "timeout": 10, "command": [
            sys.executable, "-c",
            "import pathlib, sys; sys.exit(0 if pathlib.Path('marker.txt').is_file() else 1)"]}
        self.assertTrue(self.grade_one(expectation))

    def test_command_passes_fails_on_timeout_instead_of_raising(self):
        expectation = {"type": "command_passes", "timeout": 0.2,
                       "command": [sys.executable, "-c", "import time; time.sleep(2)"]}
        self.assertFalse(self.grade_one(expectation))

    def test_the_summary_counts_skips_apart(self):
        case = {"id": "demo", "pack": "core", "prompt": "p", "expected_output": "e", "expectations": [
            {"type": "file_exists", "glob": "src/app.js", "text": "a"},
            {"type": "file_exists", "glob": "nope/*", "text": "b"},
            {"type": "transcript_reads", "pattern": "x", "text": "c"},
        ]}
        (self.case / "case.json").write_text(json.dumps(case), encoding="utf-8")
        summary = grade.grade(self.case, self.workspace, None)["summary"]
        self.assertEqual((summary["passed"], summary["failed"], summary["skipped"]), (1, 1, 1))
        self.assertEqual(summary["pass_rate"], 0.5)


class MapFindingAbsentTest(unittest.TestCase):
    """`_map_finding_absent`'s own logic, against a fixed map_structure.build_map result,
    so these tests do not depend on the naming or organization scanners' heuristics."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.case = base / "cases" / "demo"
        self.workspace = base / "workspace"
        write(self.workspace, {"src/a.js": "const a = 1;\n"})
        import map_structure
        self.map_structure = map_structure

    def tearDown(self):
        self.directory.cleanup()

    def grade_with_map(self, expectation, data):
        case = {"id": "demo", "pack": "core", "prompt": "p", "expected_output": "e",
                "expectations": [dict(expectation, text="t")]}
        self.case.mkdir(parents=True, exist_ok=True)
        (self.case / "case.json").write_text(json.dumps(case), encoding="utf-8")
        with mock.patch.object(self.map_structure, "stack_for", return_value=([], {})), \
             mock.patch.object(self.map_structure, "build_map", return_value=data):
            result = grade.grade(self.case, self.workspace, None)
        return result["expectations"][0]["passed"]

    def test_a_kind_missing_from_the_map_counts_as_zero_findings(self):
        data = {"findings": {}}
        self.assertTrue(self.grade_with_map({"type": "map_finding_absent", "kind": "comment_heavy"},
                                            data))

    def test_path_limits_the_kind_to_one_file(self):
        data = {"findings": {"names": [
            {"rule": "vague", "name": "data", "kind": "variable", "path": "src/a.js", "line": 1,
             "cites": "N1"},
            {"rule": "vague", "name": "tmp", "kind": "variable", "path": "src/b.js", "line": 2,
             "cites": "N1"},
        ]}}
        # Unscoped, either file's finding fails it.
        self.assertFalse(self.grade_with_map({"type": "map_finding_absent", "kind": "names"}, data))
        # Scoped to the file that still has a finding, it still fails.
        self.assertFalse(self.grade_with_map(
            {"type": "map_finding_absent", "kind": "names", "path": "src/a.js"}, data))
        # Scoped to a file with no finding of its own, it passes even though src/a.js and
        # src/b.js still have theirs -- this is what naming-cleanup relies on.
        self.assertTrue(self.grade_with_map(
            {"type": "map_finding_absent", "kind": "names", "path": "src/c.js"}, data))

    def test_path_matches_any_path_a_finding_names(self):
        # A duplicate group or a cycle has no `path` of its own; its members' paths count.
        data = {"findings": {
            "duplicates": [{"kind": "function", "lines": 8, "members": [
                {"path": "src/a.js", "line": 1, "symbol": "load"},
                {"path": "src/b.js", "line": 1, "symbol": "load"}]}],
            "cycles": [{"components": ["src/orders", "src/billing"], "edges": []}],
            "junk_drawer": [{"folder": "src/utils", "splits": [], "rename": None}],
        }}
        for kind, path, absent in (("duplicates", "src/b.js", False), ("duplicates", "src/c.js", True),
                                   ("cycles", "src/billing", False), ("junk_drawer", "src/utils", False),
                                   ("junk_drawer", "src/helpers", True)):
            with self.subTest(kind=kind, path=path):
                expectation = {"type": "map_finding_absent", "kind": kind, "path": path}
                self.assertEqual(self.grade_with_map(expectation, data), absent)


class SelfTestTest(unittest.TestCase):
    def test_a_case_that_passes_on_its_own_fixture_tests_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = Path(directory)
            write(cases / "vacuous" / "repo", {"src/a.js": "const a = 1;\n"})
            (cases / "vacuous" / "case.json").write_text(json.dumps({
                "id": "vacuous", "pack": "core", "prompt": "p", "expected_output": "e",
                "expectations": [{"type": "file_exists", "glob": "src/a.js", "text": "t"}],
            }), encoding="utf-8")
            problems = grade.check_cases(cases)
        self.assertTrue(any("passes on its untouched fixture" in problem for problem in problems))

    def test_command_passes_requires_a_non_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = Path(directory)
            write(cases / "cmd" / "repo", {"src/a.js": "const a = 1;\n"})
            (cases / "cmd" / "case.json").write_text(json.dumps({
                "id": "cmd", "pack": "core", "prompt": "p", "expected_output": "e",
                "expectations": [{"type": "command_passes", "command": "node --test", "text": "t"}],
            }), encoding="utf-8")
            problems = grade.check_cases(cases)
        self.assertTrue(any("non-empty list" in problem for problem in problems))

    def test_unknown_expectation_types_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = Path(directory)
            write(cases / "odd" / "repo", {"src/a.js": "const a = 1;\n"})
            (cases / "odd" / "case.json").write_text(json.dumps({
                "id": "odd", "pack": "core", "prompt": "p", "expected_output": "e",
                "expectations": [{"type": "vibes", "text": "t"}],
            }), encoding="utf-8")
            problems = grade.check_cases(cases)
        self.assertTrue(any("unknown expectation type" in problem for problem in problems))

    def test_the_shipped_cases_are_well_formed(self):
        self.assertEqual(grade.check_cases(grade.CASES_DIR), [])


if __name__ == "__main__":
    unittest.main()
