import textwrap
import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
import project_symbols


def extract(path, source):
    return project_symbols.extract(path, textwrap.dedent(source).lstrip("\n"))


def by_name(file_symbols):
    return {symbol.name: symbol for symbol in file_symbols.symbols}


class PythonTest(unittest.TestCase):
    def test_classes_functions_methods_and_privacy(self):
        result = extract("a.py", """
            class Repo(ABC):
                @abstractmethod
                def get(self): ...

            def _helper(): pass

            def load_user(): pass
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["Repo"].kind, "class")
        self.assertTrue(symbols["Repo"].exported)
        self.assertEqual(symbols["get"].kind, "method")
        self.assertEqual(symbols["get"].parent, "Repo")
        self.assertFalse(symbols["_helper"].exported)
        self.assertTrue(symbols["load_user"].exported)
        self.assertEqual((result.types, result.abstract_types), (1, 1))
        self.assertEqual(result.language, "python")

    def test_all_restricts_exports(self):
        symbols = by_name(extract("m.py", """
            __all__ = ["public"]
            def public(): pass
            def other(): pass
            """))
        self.assertTrue(symbols["public"].exported)
        self.assertFalse(symbols["other"].exported)

    def test_docstrings_become_doc_and_purpose(self):
        result = extract("svc.py", '''
            """Account services for the billing context."""

            def load_users():
                """Loads users. Cached for a minute."""
                return []
            ''')
        self.assertEqual(result.purpose, "Account services for the billing context.")
        self.assertEqual(by_name(result)["load_users"].doc, "Loads users.")

    def test_decorators_are_part_of_the_context(self):
        symbols = by_name(extract("views.py", """
            @app.get("/users")
            def list_users():
                return []
            """))
        self.assertIn('@app.get("/users")', symbols["list_users"].context)

    def test_identical_bodies_share_both_fingerprints(self):
        body = """
                total = 0
                for item in items:
                    if item.active:
                        total += item.price
                    else:
                        total -= item.discount
                return total
            """
        result = extract("dup.py", "def first(items):" + body + "\ndef second(items):" + body)
        symbols = by_name(result)
        self.assertIsNotNone(symbols["first"].exact)
        self.assertEqual(symbols["first"].exact, symbols["second"].exact)
        self.assertEqual(symbols["first"].shape, symbols["second"].shape)

    def test_renamed_copies_share_only_the_shape(self):
        first = """
            def first(items):
                total = 0
                for item in items:
                    if item.active:
                        total += item.price
                    else:
                        total -= item.discount
                return total
            """
        second = first.replace("first", "second").replace("total", "acc")
        symbols = by_name(extract("dup.py", first + "\n" + second))
        self.assertNotEqual(symbols["first"].exact, symbols["second"].exact)
        self.assertEqual(symbols["first"].shape, symbols["second"].shape)

    def test_short_functions_get_no_fingerprint(self):
        symbols = by_name(extract("s.py", "def tiny():\n    return 1\n"))
        self.assertIsNone(symbols["tiny"].exact)


class JavaScriptTest(unittest.TestCase):
    def test_typescript_classes_methods_arrows_and_exports(self):
        symbols = by_name(extract("auth.ts", """
            export class AuthService {
              verify(t: string) { return t; }
            }
            export const authMiddleware = (req, res, next) => { next(); };
            function local() {}
            """))
        self.assertEqual(symbols["AuthService"].kind, "class")
        self.assertTrue(symbols["AuthService"].exported)
        self.assertEqual((symbols["AuthService"].line, symbols["AuthService"].end_line), (1, 3))
        self.assertEqual(symbols["verify"].kind, "method")
        self.assertEqual(symbols["verify"].parent, "AuthService")
        self.assertEqual(symbols["authMiddleware"].kind, "function")
        self.assertTrue(symbols["authMiddleware"].exported)
        self.assertIn("(req, res, next)", symbols["authMiddleware"].context)
        self.assertFalse(symbols["local"].exported)

    def test_typescript_type_declarations(self):
        symbols = by_name(extract("types.ts", """
            export interface User { id: string }
            export type Id = string;
            export enum Role { A }
            """))
        self.assertEqual(
            [(symbols[name].kind, symbols[name].exported) for name in ("User", "Id", "Role")],
            [("interface", True), ("type", True), ("enum", True)],
        )

    def test_a_parenthesised_expression_is_not_an_arrow_function(self):
        symbols = by_name(extract("calc.js", "const total = (a + b) * 2;\n"))
        self.assertNotIn("total", symbols)

    def test_commonjs_exports(self):
        legacy = by_name(extract("legacy.js", """
            module.exports.requireAdmin = function (req, res, next) { next(); };
            """))
        self.assertTrue(legacy["requireAdmin"].exported)
        listed = by_name(extract("auth.js", """
            class AuthService {}
            function authMiddleware(req, res, next) { next(); }
            module.exports = { AuthService, authMiddleware };
            """))
        self.assertTrue(listed["AuthService"].exported)
        self.assertTrue(listed["authMiddleware"].exported)
        single = by_name(extract("requestId.js", """
            module.exports = function requestId(req, res, next) { next(); };
            """))
        self.assertTrue(single["requestId"].exported)

    def test_export_lists_mark_declarations_exported(self):
        symbols = by_name(extract("m.ts", """
            function a() {}
            function b() {}
            export { a };
            """))
        self.assertTrue(symbols["a"].exported)
        self.assertFalse(symbols["b"].exported)

    def test_jsdoc_becomes_doc_and_license_headers_are_not_a_purpose(self):
        result = extract("verify.ts", """
            // Copyright 2026 Example Corp. All rights reserved.

            /** Verifies tokens. Uses the shared key. */
            export function verify() {}
            """)
        self.assertEqual(by_name(result)["verify"].doc, "Verifies tokens.")
        self.assertEqual(result.purpose, "")

    def test_a_closing_brace_above_is_not_a_decorator(self):
        symbols = by_name(extract("svc.ts", """
            /** Service for auth. */
            @Injectable()
            export class AuthService {
              verify(token: string) {
                return true;
              }
              handle = async (req, res) => { res.send(1); };
            }
            export const authMiddleware = (req, res, next) => { next(); };
            """))
        self.assertEqual(symbols["AuthService"].doc, "Service for auth.")
        self.assertEqual(symbols["handle"].context.splitlines()[0].strip(),
                         "handle = async (req, res) => { res.send(1); };")
        self.assertEqual(symbols["authMiddleware"].doc, "")
        self.assertNotIn("@Injectable", symbols["authMiddleware"].context)

    def test_multiline_decorators_are_part_of_the_context(self):
        symbols = by_name(extract("app.component.ts", """
            @Component({
              selector: 'app-root',
            })
            export class AppComponent {}
            """))
        self.assertIn("@Component({", symbols["AppComponent"].context)

    def test_decorators_are_part_of_the_context(self):
        symbols = by_name(extract("users.controller.ts", """
            @Controller('users')
            export class UsersController {
              @Get()
              findAll() { return []; }
            }
            """))
        self.assertIn("@Controller(", symbols["UsersController"].context)
        self.assertEqual(symbols["findAll"].parent, "UsersController")


class SingleFileComponentTest(unittest.TestCase):
    def test_vue_file_is_a_component(self):
        result = extract("src/components/user-card.vue", """
            <template><b/></template>
            <script setup lang="ts">
            const x = 1
            </script>
            """)
        self.assertEqual(result.language, "vue")
        self.assertEqual(by_name(result)["UserCard"].kind, "component")

    def test_svelte_script_functions_are_found(self):
        result = extract("Card.svelte", """
            <script>
              export function reset() {
                return 0;
              }
            </script>
            <div>card</div>
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["Card"].kind, "component")
        self.assertEqual(symbols["reset"].line, 2)


class DispatchTest(unittest.TestCase):
    def test_unknown_extensions_are_not_extracted(self):
        self.assertIsNone(project_symbols.extract("notes.txt", "hello"))
        self.assertIsNone(project_symbols.language_of("image.png"))
        self.assertEqual(project_symbols.language_of("src/App.TSX"), "typescript")


if __name__ == "__main__":
    unittest.main()
