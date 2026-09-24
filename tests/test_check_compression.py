"""check_compression compares an original text against its compressed rewrite.

Each preserved-item kind (heading, code block, inline code, url, rule id, number)
is a fixture built to hold exactly one interesting item, so a loss can only come
from the behavior under test -- see check_compression.py's module docstring for
why the categories are independent and never reconciled against each other.
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import support  # puts the scripts folder on sys.path
import check_compression as cc


def run(*argv):
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
        code = cc.main(list(argv))
    return code, output.getvalue()


class CompareTest(unittest.TestCase):
    def test_identical_texts_lose_nothing(self):
        text = "Some plain prose about a change, nothing technical in it.\n"
        report = cc.compare(text, text)
        self.assertEqual(report.losses, [])
        self.assertEqual(report.reduction, 0.0)

    def test_dropping_filler_words_only_costs_no_losses(self):
        original = "This is a really very long sentence that says nothing important at all.\n"
        compressed = "Long sentence says nothing important.\n"
        report = cc.compare(original, compressed)
        self.assertEqual(report.losses, [])
        self.assertGreater(report.reduction, 0)

    def test_a_removed_heading_is_a_loss(self):
        original = "## Placement\n\nWhere a file lives.\n"
        compressed = "Where a file lives.\n"
        report = cc.compare(original, compressed)
        self.assertIn("heading: Placement", report.losses)

    def test_a_changed_character_inside_a_fenced_block_is_a_loss(self):
        original = "Example:\n\n```python\ndef load(path):\n    return path\n```\n"
        compressed = "Example:\n\n```python\ndef load(path):\n    return pathx\n```\n"
        report = cc.compare(original, compressed)
        self.assertEqual(len(report.losses), 1)
        self.assertTrue(report.losses[0].startswith("code block: def load(path):"))

    def test_a_removed_inline_code_span_is_a_loss(self):
        original = "Run `scripts/map_structure.py` first.\n"
        compressed = "Run it first.\n"
        report = cc.compare(original, compressed)
        self.assertIn("inline code: scripts/map_structure.py", report.losses)

    def test_a_removed_url_is_a_loss(self):
        original = "See https://example.com/a for details.\n"
        compressed = "See the docs for details.\n"
        report = cc.compare(original, compressed)
        self.assertIn("url: https://example.com/a", report.losses)

    def test_a_removed_rule_id_is_a_loss(self):
        original = "Follow G17 when naming things.\n"
        compressed = "Follow the naming rule.\n"
        report = cc.compare(original, compressed)
        self.assertIn("rule id: G17", report.losses)

    def test_a_removed_number_is_a_loss(self):
        original = "The file grew to 3,000 lines.\n"
        compressed = "The file grew large.\n"
        report = cc.compare(original, compressed)
        self.assertIn("number: 3,000", report.losses)

    def test_reduction_is_zero_when_the_original_is_empty(self):
        report = cc.compare("", "")
        self.assertEqual(report.losses, [])
        self.assertEqual(report.reduction, 0.0)

    def test_losses_are_ordered_as_they_first_appear_in_the_original(self):
        # The url sits before the rule id in the source text; the report must
        # keep that order rather than, say, grouping by category.
        original = "See https://example.com/a and read G17 as well.\n"
        compressed = "See nothing here.\n"
        report = cc.compare(original, compressed)
        self.assertEqual(report.losses, ["url: https://example.com/a", "rule id: G17"])

    def test_heading_with_trailing_hashes_normalizes_correctly(self):
        # CommonMark allows trailing # marks in headings; they should be stripped
        # so "## Placement ##" normalizes the same as "## Placement".
        original = "## Placement ##\n\nText.\n"
        compressed = "## Placement\n\nText.\n"
        report = cc.compare(original, compressed)
        self.assertEqual(report.losses, [])

    def test_url_with_trailing_sentence_punctuation_is_not_lost(self):
        # A bare URL at sentence end picks up incidental punctuation from the regex.
        # "https://example.com/a." should be treated as "https://example.com/a"
        # when comparing, so moving it out of sentence position is not a loss.
        original = "Read https://example.com/a.\n"
        compressed = "Read https://example.com/a\n"
        report = cc.compare(original, compressed)
        self.assertEqual(report.losses, [])

    def test_removing_a_url_entirely_is_still_a_loss(self):
        # Stripping trailing punctuation should not mask actual URL removal.
        original = "Read https://example.com/a.\n"
        compressed = "Read the docs.\n"
        report = cc.compare(original, compressed)
        self.assertIn("url: https://example.com/a", report.losses)

    def test_a_marker_of_the_other_kind_stays_inside_the_block(self):
        original = "```text\nline1\n~~~\n# not a heading\n```\n"
        report = cc.compare(original, original.replace("~~~\n", ""))
        self.assertEqual(report.losses, ["code block: line1"])

    def test_a_longer_closing_run_closes_the_block(self):
        original = "```\ncode\n````\n## After\n"
        report = cc.compare(original, "```\ncode\n````\n")
        self.assertEqual(report.losses, ["heading: After"])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_a_missing_file_is_a_read_error(self):
        original = self.write("original.md", "hello\n")
        missing = str(self.root / "missing.md")
        code, _ = run(original, missing)
        self.assertEqual(code, 2)

    def test_a_loss_prints_each_loss_on_its_own_line_then_the_summary(self):
        original = self.write("original.md", "## Placement\n\nSee G17 for the rule.\n")
        compressed = self.write("compressed.md", "See the rule.\n")
        code, output = run(original, compressed)
        self.assertEqual(code, 1)
        lines = output.splitlines()
        self.assertIn("heading: Placement", lines)
        self.assertIn("rule id: G17", lines)
        self.assertTrue(lines[-1].startswith("2 lost:"))

    def test_nothing_lost_prints_one_summary_line_and_exits_zero(self):
        original = self.write("original.md", "Plain prose, nothing technical.\n")
        compressed = self.write("compressed.md", "Plain prose.\n")
        code, output = run(original, compressed)
        self.assertEqual(code, 0)
        self.assertEqual(len(output.splitlines()), 1)
        self.assertTrue(output.startswith("nothing lost:"))

    def test_json_reports_losses_and_token_counts(self):
        original = self.write("original.md", "## Placement\n\nSee G17 for the rule.\n")
        compressed = self.write("compressed.md", "See the rule.\n")
        code, output = run(original, compressed, "--json")
        self.assertEqual(code, 1)
        data = json.loads(output)
        self.assertEqual(set(data), {"losses", "original_tokens", "compressed_tokens", "reduction"})
        self.assertIn("heading: Placement", data["losses"])


if __name__ == "__main__":
    unittest.main()
