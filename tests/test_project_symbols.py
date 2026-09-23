import textwrap
import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
import project_symbols


def extract(path, source):
    return project_symbols.extract(path, textwrap.dedent(source).lstrip("\n"))


def by_name(file_symbols):
    """First symbol per name; symbols are sorted by line, so a class wins over its constructor."""
    found = {}
    for symbol in file_symbols.symbols:
        found.setdefault(symbol.name, symbol)
    return found


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


class JvmTest(unittest.TestCase):
    def test_java_annotated_class_and_methods(self):
        symbols = by_name(extract("UserController.java", """
            @RestController
            public class UserController {
              public UserController(UserService service) {}
              public List<User> all() { return List.of(); }
            }
            """))
        self.assertEqual(symbols["UserController"].kind, "class")
        self.assertIn("@RestController", symbols["UserController"].context)
        self.assertEqual(symbols["all"].parent, "UserController")
        self.assertTrue(symbols["UserController"].exported)

    def test_java_interface_methods_have_no_body(self):
        result = extract("OrderPort.java", """
            public interface OrderPort {
              void save(Order o);
            }
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["OrderPort"].kind, "interface")
        self.assertEqual(symbols["save"].kind, "method")
        self.assertIsNone(symbols["save"].exact)
        self.assertEqual(result.abstract_types, 1)

    def test_java_enum_constants_are_not_methods(self):
        symbols = by_name(extract("Color.java", """
            public enum Color {
              RED("r"),
              GREEN("g");
              Color(String code) {}
            }
            """))
        self.assertNotIn("RED", symbols)
        self.assertEqual(symbols["Color"].kind, "enum")

    def test_kotlin_classes_extension_functions_and_objects(self):
        symbols = by_name(extract("Svc.kt", """
            @Service
            class OrderService(private val repo: Repo) {
              suspend fun place(o: Order) { repo.save(o) }
            }
            fun String.slug() = lowercase()
            internal object Cache
            private fun hidden() {}
            enum class Level { LOW }
            """))
        self.assertIn("@Service", symbols["OrderService"].context)
        self.assertEqual(symbols["place"].parent, "OrderService")
        self.assertEqual((symbols["slug"].kind, symbols["slug"].exported), ("function", True))
        self.assertEqual((symbols["Cache"].kind, symbols["Cache"].exported), ("object", True))
        self.assertFalse(symbols["hidden"].exported)
        self.assertEqual(symbols["Level"].kind, "enum")

    def test_scala_traits_case_classes_and_objects(self):
        result = extract("Model.scala", """
            sealed trait Shape
            case class Circle(r: Double) extends Shape
            object Shape {
              def unit: Shape = Circle(1)
            }
            """)
        kinds = {(symbol.name, symbol.kind) for symbol in result.symbols}
        self.assertTrue({("Shape", "trait"), ("Circle", "class"), ("Shape", "object"),
                         ("unit", "method")} <= kinds)
        self.assertEqual(result.abstract_types, 1)

    def test_scala_3_braceless_members(self):
        symbols = by_name(extract("Greeter.scala", """
            class Greeter(name: String):
              def greet(): String =
                s"Hello $name"
              def bye(): String = "bye"

            def top(): Int = 1
            """))
        self.assertEqual(symbols["Greeter"].end_line, 4)
        self.assertEqual(symbols["greet"].parent, "Greeter")
        self.assertEqual(symbols["bye"].parent, "Greeter")
        self.assertIsNone(symbols["top"].parent)


class DotnetTest(unittest.TestCase):
    def test_types_inside_a_namespace_block_are_top_level(self):
        symbols = by_name(extract("Orders.cs", """
            namespace App.Web {
              [ApiController]
              public sealed class OrdersController : ControllerBase {
                public async Task<IActionResult> Get(CancellationToken ct) { return Ok(); }
                private void Log() {}
              }
            }
            """))
        controller = symbols["OrdersController"]
        self.assertIsNone(controller.parent)
        self.assertIn("[ApiController]", controller.context)
        self.assertIn("ControllerBase", controller.context)
        self.assertEqual(symbols["Get"].parent, "OrdersController")
        self.assertTrue(symbols["Get"].exported)
        self.assertFalse(symbols["Log"].exported)

    def test_records_and_interfaces_with_a_file_scoped_namespace(self):
        result = extract("File.cs", """
            namespace App.Domain;
            public record Money(decimal Amount);
            public interface IClock { DateTime Now { get; } }
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["Money"].kind, "record")
        self.assertEqual(symbols["IClock"].kind, "interface")
        self.assertEqual(result.abstract_types, 1)


class PhpTest(unittest.TestCase):
    def test_attributes_classes_and_methods(self):
        symbols = by_name(extract("Authenticate.php", """
            <?php
            namespace App\Http\Middleware;
            #[Attr]
            final class Authenticate {
              public function handle($request, Closure $next) { return $next($request); }
              private function check() {}
            }
            trait Loggable {}
            """))
        self.assertIn("#[Attr]", symbols["Authenticate"].context)
        self.assertEqual(symbols["handle"].parent, "Authenticate")
        self.assertTrue(symbols["handle"].exported)
        self.assertFalse(symbols["check"].exported)
        self.assertEqual(symbols["Loggable"].kind, "trait")
        self.assertFalse(symbols["Loggable"].abstract)


class DartTest(unittest.TestCase):
    def test_widgets_constructors_and_privacy(self):
        result = extract("login_page.dart", """
            class LoginPage extends StatelessWidget {
              const LoginPage({super.key});
              @override
              Widget build(BuildContext context) { return Text(''); }
            }
            abstract interface class AuthRepo { Future<User> login(); }
            String _hidden() => '';
            extension StringX on String {
              String shout() => toUpperCase();
            }
            """)
        symbols = by_name(result)
        self.assertIn("StatelessWidget", symbols["LoginPage"].context)
        self.assertEqual(symbols["build"].parent, "LoginPage")
        self.assertIn("@override", symbols["build"].context)
        self.assertTrue(symbols["AuthRepo"].abstract)
        self.assertFalse(symbols["_hidden"].exported)
        self.assertNotIn("StringX", symbols)
        self.assertEqual(symbols["shout"].parent, "StringX")


def owners(file_symbols):
    return {(symbol.name, symbol.parent) for symbol in file_symbols.symbols}


class GoTest(unittest.TestCase):
    def test_functions_receivers_interfaces_and_package_doc(self):
        result = extract("auth.go", """
            // Package auth verifies tokens.
            package auth

            // AuthMiddleware checks tokens.
            func AuthMiddleware(next http.Handler) http.Handler { return next }

            type Store interface {
            	Get(id string) (User, error)
            }

            func (s *userStore) Get(id string) (User, error) { return User{}, nil }

            func helper() {}
            """)
        symbols = by_name(result)
        self.assertEqual(result.purpose, "Package auth verifies tokens.")
        self.assertTrue(symbols["AuthMiddleware"].exported)
        self.assertEqual(symbols["AuthMiddleware"].doc, "AuthMiddleware checks tokens.")
        self.assertEqual((symbols["Store"].kind, symbols["Store"].abstract), ("interface", True))
        self.assertEqual((symbols["Get"].kind, symbols["Get"].parent), ("method", "userStore"))
        self.assertFalse(symbols["helper"].exported)


class RustTest(unittest.TestCase):
    def test_traits_impls_visibility_and_test_modules(self):
        result = extract("lib.rs", """
            pub trait Repo {
                fn get(&self) -> u8;
            }
            pub struct Pg;
            impl Repo for Pg {
                fn get(&self) -> u8 { 1 }
            }
            fn private() {}
            #[cfg(test)]
            mod tests {
                #[test]
                fn t() {}
            }
            """)
        symbols = by_name(result)
        self.assertEqual((symbols["Repo"].kind, symbols["Repo"].abstract), ("trait", True))
        self.assertEqual(symbols["Pg"].kind, "struct")
        self.assertIn(("get", "Pg"), owners(result))
        self.assertIn(("get", "Repo"), owners(result))
        self.assertFalse(symbols["private"].exported)
        self.assertNotIn("t", symbols)
        self.assertNotIn("tests", symbols)


class SwiftTest(unittest.TestCase):
    def test_views_protocols_extensions_and_access(self):
        result = extract("ContentView.swift", """
            struct ContentView: View {
                var body: some View { Text("") }
            }
            protocol Clock { func now() -> Date }
            extension ContentView {
                func refresh() {}
            }
            private func hidden() {}
            final class Store {
                init(name: String) {}
                class func make() -> Store { Store(name: "") }
            }
            """)
        symbols = by_name(result)
        self.assertIn(": View", symbols["ContentView"].context)
        self.assertEqual((symbols["Clock"].kind, symbols["Clock"].abstract), ("protocol", True))
        self.assertEqual(symbols["refresh"].parent, "ContentView")
        self.assertNotIn("func", symbols)
        self.assertFalse(symbols["hidden"].exported)
        self.assertEqual(symbols["init"].parent, "Store")
        self.assertEqual(symbols["make"].parent, "Store")


class CFamilyTest(unittest.TestCase):
    def test_c_definitions_and_linkage(self):
        symbols = by_name(extract("list.c", """
            static int grow(list *l) {
              return 0;
            }
            int
            list_push(list *l, int v)
            {
              return grow(l);
            }
            """))
        self.assertFalse(symbols["grow"].exported)
        self.assertTrue(symbols["list_push"].exported)
        self.assertEqual(symbols["list_push"].end_line, 8)

    def test_headers_with_only_declarations_have_no_symbols(self):
        result = extract("list.h", """
            typedef struct list list;
            int list_push(list *l, int v);
            """)
        self.assertEqual(result.symbols, [])

    def test_cpp_classes_namespaces_and_qualified_methods(self):
        result = extract("shape.cpp", """
            namespace geo {
            class Shape {
            public:
              virtual double area() const = 0;
            };
            double Circle::area() const { return 1; }
            }
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["Shape"].kind, "class")
        self.assertTrue(symbols["Shape"].abstract)
        self.assertIn(("area", "Shape"), owners(result))
        self.assertIn(("area", "Circle"), owners(result))

    def test_objective_c_interfaces_and_implementations(self):
        result = extract("OrderService.m", """
            @interface OrderService : NSObject
            - (void)place:(Order *)o;
            @end
            @implementation OrderService
            - (void)place:(Order *)o {
            }
            @end
            """)
        symbols = by_name(result)
        self.assertEqual(symbols["OrderService"].kind, "class")
        self.assertEqual({parent for name, parent in owners(result) if name == "place"},
                         {"OrderService"})


class DispatchTest(unittest.TestCase):
    def test_unknown_extensions_are_not_extracted(self):
        self.assertIsNone(project_symbols.extract("notes.txt", "hello"))
        self.assertIsNone(project_symbols.language_of("image.png"))
        self.assertEqual(project_symbols.language_of("src/App.TSX"), "typescript")


if __name__ == "__main__":
    unittest.main()
