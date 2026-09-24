import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
from source import lexer as source_lexer


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

    def test_deeply_nested_template_literals_do_not_overflow(self):
        text = "const a = " + "`${" * 5000 + "}`" * 5000 + ";\nfunction after() {}\n"
        self.assertTrue(source_lexer.strip(text, "javascript").code.endswith("function after() {}\n"))

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

    def test_a_lifetime_followed_by_a_quote_is_kept(self):
        for text in ("impl<'a> Parser<'a> {", "fn first<T>(xs: &'_ [T], d: &'_ T) -> &'_ T {"):
            with self.subTest(text=text):
                self.assertEqual(source_lexer.strip(text, "rust").code, text)

    def test_char_literals_are_one_character_or_one_escape(self):
        text = "let a = '{'; let b = '\\u{7D}'; let c = b'}'; let d = '\\'';"
        code = source_lexer.strip(text, "rust").code
        self.assertEqual((code.count("{"), code.count("}"), code.count("'")), (0, 0, 8))

    def test_jsx_closing_tags_do_not_start_a_regex(self):
        for text in ("{props.open && <p>Hi</p>} <span>menu</span>",
                     "<label>Name</label>{this.props.name && <b>{this.props.name}</b>}",
                     "<Foo a={b} />{c && <i>x</i>}"):
            with self.subTest(text=text):
                code = source_lexer.strip(text, "javascript").code
                self.assertEqual(code, text)

    def test_a_regex_after_a_spaced_less_than_is_still_a_regex(self):
        text = "if (a < /}/.test(s)) {}"
        self.assertEqual(source_lexer.strip(text, "javascript").code.count("}"), 1)

    def test_ruby_regex_literals_hide_their_quotes(self):
        text = "line[/require ['\"](.+)['\"]/, 1]\nx = s.gsub(/\"/, '')\ndef after; end\n"
        code = source_lexer.strip(text, "ruby").code
        self.assertIn("def after; end", code)
        self.assertNotIn("require", code)

    def test_ruby_percent_literals_hide_their_contents(self):
        text = "A = %w[it's a]\nB = %q(don't {)\nC = %r{a/b}\nputs %(say \"hi\")\ndef after; end\n"
        code = source_lexer.strip(text, "ruby").code
        self.assertIn("def after; end", code)
        self.assertNotIn("'", code)
        self.assertEqual(code.count("{"), 1)

    def test_ruby_division_is_not_a_regex(self):
        text = "half = total / 2\nrate = (a + b) / count / 3\n"
        self.assertEqual(source_lexer.strip(text, "ruby").code, text)

    def test_a_shell_shift_is_not_a_heredoc(self):
        text = "mask=$(( 1 << bit ))\n(( flags <<= 2 ))\necho }\n"
        self.assertEqual(source_lexer.strip(text, "shell").code, text)

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
