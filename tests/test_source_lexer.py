import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
import source_lexer


def body_pair(text, language):
    stripped = source_lexer.strip(text, language)
    return source_lexer.match_braces(stripped.code)


class StripTest(unittest.TestCase):
    def test_offsets_and_lines_are_preserved(self):
        text = "const a = 'x'; // note\n/* block\n comment */ let b = \"y\";\n"
        stripped = source_lexer.strip(text, "javascript")
        self.assertEqual(len(stripped.code), len(text))
        self.assertEqual(len(stripped.no_comments), len(text))
        self.assertEqual(stripped.code.count("\n"), text.count("\n"))

    def test_code_blanks_comments_and_strings_but_no_comments_keeps_strings(self):
        text = 'x = "keep" // drop\n'
        stripped = source_lexer.strip(text, "javascript")
        self.assertNotIn("keep", stripped.code)
        self.assertNotIn("drop", stripped.code)
        self.assertIn('"keep"', stripped.no_comments)
        self.assertNotIn("drop", stripped.no_comments)

    def test_a_brace_inside_a_comment_does_not_count(self):
        text = "function a() {\n  // }\n  return 1;\n}\n"
        self.assertEqual(body_pair(text, "javascript")[text.index("{")], text.rindex("}"))

    def test_a_brace_inside_a_string_does_not_count(self):
        text = 'function a() { return "}"; }'
        self.assertEqual(body_pair(text, "javascript")[text.index("{")], text.rindex("}"))

    def test_template_literals_are_blanked(self):
        text = "const s = `a ${b} {`;\nfunction f() {}\n"
        stripped = source_lexer.strip(text, "typescript")
        self.assertEqual(stripped.code.count("{"), 1)

    def test_regex_literals_are_blanked(self):
        text = "const r = /[{]/g;\nfunction f() {}\n"
        stripped = source_lexer.strip(text, "javascript")
        self.assertEqual(stripped.code.count("{"), 1)

    def test_python_triple_quoted_strings_are_blanked(self):
        text = 'def f():\n    """doc { """\n    return 1\n'
        self.assertNotIn("{", source_lexer.strip(text, "python").code)

    def test_shell_hash_inside_a_word_is_not_a_comment(self):
        text = "echo ${#arr[@]} # count\n"
        code = source_lexer.strip(text, "shell").code
        self.assertIn("${#arr[@]}", code)
        self.assertNotIn("count", code)

    def test_shell_heredoc_bodies_are_blanked(self):
        text = "cat <<EOF\n}\nEOF\necho }\n"
        code = source_lexer.strip(text, "shell").code
        self.assertEqual(code.count("}"), 1)

    def test_rust_lifetimes_are_not_strings(self):
        text = "fn a<'a>(x: &'a str) -> &'a str { x }"
        self.assertEqual(body_pair(text, "rust")[text.index("{")], text.rindex("}"))

    def test_php_attributes_stay_code(self):
        text = "#[Route('/x')]\nclass A {}\n"
        self.assertIn("#[Route", source_lexer.strip(text, "php").code)

    def test_csharp_verbatim_strings_end_at_a_single_quote(self):
        text = 'var p = @"C:\\x\\"; class A { }'
        self.assertEqual(body_pair(text, "csharp")[text.index("{")], text.rindex("}"))

    def test_powershell_block_comments_are_blanked(self):
        text = "<#\n}\n#>\nfunction A { }\n"
        code = source_lexer.strip(text, "powershell").code
        self.assertEqual(code.count("}"), 1)


if __name__ == "__main__":
    unittest.main()
