import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_transcript_reads_is_skipped_without_a_transcript(self):
        expectation = {"type": "transcript_reads", "pattern": r"frameworks/express\.md"}
        self.assertIsNone(self.grade_one(expectation))
        transcript = self.workspace.parent / "transcript.txt"
        transcript.write_text("Read skills/clean-code/references/frameworks/express.md\n",
                              encoding="utf-8")
        self.assertTrue(self.grade_one(expectation, transcript))

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
