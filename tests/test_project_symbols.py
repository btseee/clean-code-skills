import textwrap
import time
import unittest
from unittest import mock

import support  # noqa: F401  (puts the scripts folder on sys.path)
import symbols as project_symbols


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

    def test_a_file_this_python_cannot_parse_says_so(self):
        # Newer syntax than the running interpreter reads, or simply broken code.
        result = extract("orders.py", """
            class OrderParser:
                def parse(self, text:
                    return 1
            """)
        self.assertEqual(result.symbols, [])
        self.assertRegex(result.unparsed, r"SyntaxError.*line \d+")
        self.assertEqual(extract("fine.py", "x = 1\n").unparsed, "")

    def test_a_parser_that_gives_up_marks_the_file_instead_of_crashing(self):
        with mock.patch("symbols.python_source.ast.parse", side_effect=RecursionError("too deep")):
            result = extract("strings.py", "TABLE = 'a' + 'b'\n")
        self.assertEqual(result.symbols, [])
        self.assertIn("RecursionError", result.unparsed)


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

    def test_braces_in_the_parameter_list_are_not_the_body(self):
        result = extract("card.tsx", """
            export function UserCard({ user, onSelect }) {
              const a = 1;
              return a;
            }
            export const Badge = ({ label }) => {
              return label;
            };
            function update(opts: { id: string }) {
              return opts.id;
            }
            function save(
              order,
              options,
            ) {
              return order;
            }
            """)
        self.assertEqual({symbol.name: (symbol.line, symbol.end_line) for symbol in result.symbols},
                         {"UserCard": (1, 4), "Badge": (5, 7), "update": (8, 10), "save": (11, 16)})

    def test_an_arrow_returning_an_object_literal_spans_the_literal(self):
        symbols = by_name(extract("factories.ts", """
            export const createApi = (http: Client) => ({
              orders: orders(http),
              users: users(http),
            });
            """))
        self.assertEqual(symbols["createApi"].end_line, 4)

    def test_jsx_closing_tags_keep_later_declarations(self):
        layout = extract("Layout.jsx", """
            export function Header(props) {
              return (
                <nav>
                  {props.open && <p>Hi</p>} <span>menu</span>
                </nav>
              );
            }

            export function Footer() {
              return <footer />;
            }

            export const Sidebar = () => {
              return <aside />;
            };
            """)
        self.assertEqual([symbol.name for symbol in layout.symbols], ["Header", "Footer", "Sidebar"])
        profile = by_name(extract("Profile.jsx", """
            export class Profile extends React.Component {
              render() {
                return (
                  <div>
                    <label>Name</label>{this.props.name && <b>{this.props.name}</b>}
                  </div>
                );
              }

              handleClick() {
                this.setState({ open: true });
              }
            }
            """))
        self.assertEqual(profile["Profile"].end_line, 13)
        self.assertEqual(profile["handleClick"].parent, "Profile")

    def test_destructured_parameters_do_not_hide_duplicate_bodies(self):
        body = """
              let total = 0;
              for (const item of items) {
                total += item.price * item.qty;
              }
              return total * (1 + rate);
            }
            """
        symbols = by_name(extract("totals.js", "function cartTotal({ items, rate }) {" + body +
                                  "function checkoutTotal({ items, rate }) {" + body))
        self.assertIsNotNone(symbols["cartTotal"].exact)
        self.assertEqual(symbols["cartTotal"].exact, symbols["checkoutTotal"].exact)

    def test_a_decorator_on_the_member_line(self):
        symbols = by_name(extract("app.component.ts", """
            export class AppComponent {
              @HostListener('window:resize') onResize() {
                this.width = 1;
              }
              @Input() onChange = (value) => {
                this.value = value;
              };
            }
            """))
        self.assertEqual((symbols["onResize"].parent, symbols["onResize"].end_line), ("AppComponent", 4))
        self.assertEqual(symbols["onChange"].parent, "AppComponent")

    def test_an_exported_function_expression_is_not_a_namespace(self):
        symbols = by_name(extract("routes.js", """
            module.exports = function (app) {
              function authenticate(req, res, next) {
                next();
              }
              app.use(authenticate);
            };
            global.setup = function () {
              function seedDatabase() {
                return 1;
              }
            };
            """))
        self.assertEqual(symbols, {})
        declared = by_name(extract("types.d.ts", """
            declare module 'express' {
              export function helper(): void;
            }
            declare global {
              function gfn(): void;
            }
            namespace A.B {
              export function inner() {}
            }
            """))
        self.assertEqual(sorted(declared), ["gfn", "helper", "inner"])

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

    def test_annotations_on_the_declaration_line(self):
        java = owners(extract("Point.java", """
            public class Point {
                @Override public String toString() {
                    return "p";
                }

                @Override
                public int hashCode() {
                    return 1;
                }

                @Inject public Point(Clock clock) {}
            }
            """))
        self.assertTrue({("toString", "Point"), ("hashCode", "Point"), ("Point", "Point")} <= java)
        kotlin = by_name(extract("Greeting.kt", """
            @Composable fun Greeting(name: String) {
                Text(name)
            }
            """))
        self.assertEqual(kotlin["Greeting"].end_line, 3)

    def test_a_kotlin_lambda_default_is_not_the_body(self):
        symbols = by_name(extract("Retry.kt", """
            fun retry(times: Int, block: () -> Unit = {}) {
                repeat(times) { block() }
            }
            """))
        self.assertEqual(symbols["retry"].end_line, 3)

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

    def test_a_byte_order_mark_does_not_hide_the_namespace(self):
        symbols = by_name(extract("RelayCommand.cs",
                                  "﻿namespace Gui\n{\n    public class RelayCommand\n    {\n"
                                  "        public void Run() {}\n    }\n}\n"))
        self.assertIsNone(symbols["RelayCommand"].parent)
        self.assertEqual(symbols["Run"].parent, "RelayCommand")

    def test_attributes_on_the_declaration_line(self):
        symbols = by_name(extract("OrdersController.cs", """
            [ApiController]
            public class OrdersController : ControllerBase
            {
                [HttpGet("{id}")] public async Task<IActionResult> Get(int id)
                {
                    return Ok(id);
                }

                [HttpPost]
                public IActionResult Create(Order order)
                {
                    return Ok(order);
                }
            }
            """))
        self.assertEqual((symbols["Get"].parent, symbols["Get"].end_line), ("OrdersController", 7))
        self.assertEqual(symbols["Create"].parent, "OrdersController")

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
            namespace App\\Http\\Middleware;
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

    def test_braced_namespaces_with_a_backslash_are_transparent(self):
        result = extract("billing.php", """
            <?php
            namespace App\\Billing {
                class Invoice {
                    public function total() { return 1; }
                }
            }

            namespace App {
                class Kernel {
                    public function boot() { return 2; }
                }
            }
            """)
        self.assertTrue({("Invoice", None), ("total", "Invoice"), ("Kernel", None),
                         ("boot", "Kernel")} <= owners(result))


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

    def test_calls_inside_initializers_are_not_functions(self):
        result = extract("router.dart", """
            final router = GoRouter(
              routes: [
                GoRoute(
                  path: '/',
                  builder: (context, state) => const HomeScreen(),
                ),
              ],
            );

            final pages = [
              HomeScreen(),
              SettingsScreen(),
            ];

            class Menu {
              final items = [
                MenuItem(),
              ];
              void open() {}
            }

            void main() {
              runApp(App());
            }
            """)
        self.assertEqual({(symbol.name, symbol.parent) for symbol in result.symbols},
                         {("Menu", None), ("open", "Menu"), ("main", None)})

    def test_named_parameters_are_not_the_body(self):
        result = extract("greeting.dart", """
            class Greeting extends StatelessWidget {
              Greeting({super.key, required this.name}) {
                print(name);
              }
              final String name;
            }

            void greet({required String name, int times = 1}) {
              for (var i = 0; i < times; i++) {
                print(name);
              }
            }
            """)
        extents = {(symbol.name, symbol.kind): (symbol.line, symbol.end_line)
                   for symbol in result.symbols}
        self.assertEqual(extents[("Greeting", "method")], (2, 4))
        self.assertEqual(extents[("greet", "function")], (8, 12))


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

    def test_type_literals_in_a_signature_are_not_the_body(self):
        result = extract("cache.go", """
            package cache

            func Print(v interface{}) error {
            	return nil
            }

            func (c *Cache) Get(key string) interface{} {
            	return c.items[key]
            }

            func Dump(v struct{ A int }) map[string]interface{} {
            	return nil
            }
            """)
        self.assertEqual({symbol.name: (symbol.line, symbol.end_line) for symbol in result.symbols},
                         {"Print": (3, 5), "Get": (7, 9), "Dump": (11, 13)})


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

    def test_impl_blocks_with_lifetimes_keep_their_methods(self):
        result = extract("parser.rs", """
            pub struct Parser<'a> {
                input: &'a str,
            }

            impl<'a> Parser<'a> {
                pub fn new(input: &'a str) -> Self {
                    Parser { input }
                }
            }

            impl<'a> From<&'a str> for Name<'a> {
                fn from(value: &'a str) -> Self { Name(value) }
            }

            impl<T: AsRef<str>> Label<T> {
                fn text(&self) -> &str { self.0.as_ref() }
            }

            pub fn first<T>(xs: &'_ [T], d: &'_ T) -> &'_ T {
                xs.first().unwrap_or(d)
            }
            """)
        self.assertTrue({("new", "Parser"), ("from", "Name"), ("text", "Label")} <= owners(result))
        self.assertEqual(by_name(result)["first"].end_line, 21)

    def test_where_clauses_at_the_declaration_indentation(self):
        # rustfmt puts `where` at the declaration's own indentation.
        result = extract("store.rs", """
            pub fn process<T>(items: &[T]) -> Vec<T>
            where
                T: Clone,
            {
                let mut out = Vec::new();
                for item in items {
                    out.push(item.clone());
                }
                out
            }

            impl<T> Store<T>
            where
                T: Clone,
            {
                pub fn get(&self) -> Option<T> {
                    None
                }
            }
            """)
        self.assertEqual(by_name(result)["process"].end_line, 10)
        self.assertIn(("get", "Store"), owners(result))


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

    def test_the_doc_above_an_export_macro_belongs_to_the_function(self):
        source = """
            /* Splits x into a fraction and a power of two. */
            NUMBA_EXPORT_FUNC(double)
            numba_frexp(double x, int *exp)
            {
                return x;
            }
            """
        for path in ("helper.c", "helper.cpp"):
            with self.subTest(path=path):
                [symbol] = extract(path, source).symbols
                self.assertEqual((symbol.name, symbol.doc),
                                 ("numba_frexp", "Splits x into a fraction and a power of two."))

    def test_attribute_lines_are_not_functions(self):
        source = """
            __attribute__((noinline))
            static int parse_header(const char *buf, size_t len)
            {
                return 0;
            }

            __declspec(dllexport)
            int compute_checksum(const unsigned char *data, int n)
            {
                return n;
            }

            __attribute__((unused)) static void trace(void) {
            }
            """
        for path in ("parse.c", "parse.cpp"):
            with self.subTest(path=path):
                symbols = by_name(extract(path, source))
                self.assertEqual(sorted(symbols), ["compute_checksum", "parse_header", "trace"])
                self.assertEqual((symbols["parse_header"].line, symbols["parse_header"].end_line),
                                 (2, 5))
                self.assertFalse(symbols["parse_header"].exported)
                self.assertTrue(symbols["compute_checksum"].exported)
                self.assertFalse(symbols["trace"].exported)

    def test_cpp_constructors_with_initializer_lists(self):
        result = extract("point.cpp", """
            Point::Point(int x, int y)
                : x_(x),
                  y_{y}
            {
            }

            Point::Point(const Point& other) : x_(std::move(other.x_)), y_(other.y_) {}
            """)
        self.assertEqual([(s.name, s.parent, s.line, s.end_line) for s in result.symbols],
                         [("Point", "Point", 1, 5), ("Point", "Point", 7, 7)])

    def test_cpp_classes_behind_export_macros(self):
        result = extract("render.h", """
            class MYLIB_API Renderer : public Base {
            public:
                void draw() {}
            };

            class Q_CORE_EXPORT Timer {
            public:
                void start() {}
            };

            struct __declspec(dllexport) Point {
                int x;
            };
            """)
        self.assertTrue({("Renderer", None), ("draw", "Renderer"), ("Timer", None), ("start", "Timer"),
                         ("Point", None)} <= owners(result))

    def test_an_access_label_is_not_part_of_the_next_member(self):
        symbols = by_name(extract("scene.h", """
            class Scene {
            public:
                /// Draws every visible node.
                void draw();
            };
            """))
        self.assertEqual((symbols["draw"].line, symbols["draw"].doc), (4, "Draws every visible node."))

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


class RubyTest(unittest.TestCase):
    def test_classes_modules_methods_and_docs(self):
        result = extract("order_service.rb", """
            # frozen_string_literal: true

            # Places orders.
            class OrderService < BaseService
              def call(order)
                save(order)
              end
            end
            module Billing
              def self.charge; end
            end
            """)
        symbols = by_name(result)
        self.assertEqual(result.purpose, "")
        self.assertEqual(symbols["OrderService"].kind, "class")
        self.assertIn("< BaseService", symbols["OrderService"].context)
        self.assertEqual(symbols["OrderService"].doc, "Places orders.")
        self.assertEqual(symbols["OrderService"].end_line, 8)
        self.assertEqual(symbols["call"].parent, "OrderService")
        self.assertEqual(symbols["Billing"].kind, "module")
        self.assertEqual((symbols["charge"].parent, symbols["charge"].end_line), ("Billing", 10))

    def test_method_level_rescue_and_ensure_stay_in_the_method(self):
        symbols = by_name(extract("orders_controller.rb", """
            class OrdersController < ApplicationController
              def show
                @order = Order.find(params[:id])
                render json: @order
              rescue ActiveRecord::RecordNotFound
                head :not_found
              end

              def destroy
                @order.destroy
              ensure
                cleanup
              end
            end
            """))
        self.assertEqual((symbols["show"].line, symbols["show"].end_line), (2, 7))
        self.assertEqual((symbols["destroy"].line, symbols["destroy"].end_line), (9, 13))

    def test_methods_that_differ_only_in_their_rescue_are_not_identical(self):
        body = "    a = load(params)\n    b = transform(a)\n    c = save(b)\n    log(c)\n    notify(c)\n"
        symbols = by_name(project_symbols.extract("jobs.rb", (
            "class Jobs\n  def one\n" + body + "  rescue KeyError\n    head :bad_request\n  end\n\n"
            "  def two\n" + body + "  rescue IOError\n    retry_later\n  end\nend\n")))
        self.assertIsNotNone(symbols["one"].exact)
        self.assertNotEqual(symbols["one"].exact, symbols["two"].exact)

    def test_a_quote_inside_a_regex_does_not_swallow_the_file(self):
        result = extract("loader.rb", """
            class Loader
              def requires(line)
                line[/require ['"](.+)['"]/, 1]
              end

              def load_all
                files.each { |f| load f }
              end
            end

            class Other
              def run
                1
              end
            end
            """)
        self.assertEqual([(symbol.name, symbol.end_line) for symbol in result.symbols],
                         [("Loader", 9), ("requires", 4), ("load_all", 8), ("Other", 15),
                          ("run", 14)])

    def test_classes_inside_namespacing_modules_are_top_level(self):
        symbols = by_name(extract("users_controller.rb", """
            module Admin
              class UsersController < ApplicationController
                def index
                  @users = User.all
                end
              end
            end
            """))
        self.assertIsNone(symbols["UsersController"].parent)
        self.assertEqual(symbols["index"].parent, "UsersController")


class ScriptTest(unittest.TestCase):
    def test_shell_functions_and_heredocs(self):
        symbols = by_name(extract("deploy.sh", """
            #!/usr/bin/env bash
            # Deploys the app.
            log() {
              echo "$1" >&2
            }
            function main {
              cat <<EOF
            }
            EOF
              log hi
            }
            """))
        self.assertEqual(symbols["log"].kind, "function")
        self.assertEqual(symbols["main"].end_line, 11)

    def test_a_shift_in_arithmetic_is_not_a_heredoc(self):
        result = extract("bits.sh", """
            #!/bin/bash
            set_bit() {
              local mask=$(( 1 << bit ))
              echo "$mask"
            }

            clear_bit() {
              local mask=$(( ~(1 << bit) ))
              echo "$mask"
            }
            """)
        self.assertEqual([(symbol.name, symbol.line, symbol.end_line) for symbol in result.symbols],
                         [("set_bit", 2, 5), ("clear_bit", 7, 10)])

    def test_powershell_functions_help_and_classes(self):
        symbols = by_name(extract("Tools.psm1", """
            function Get-Thing {
              <#
              .SYNOPSIS
              Returns things.
              #>
              [CmdletBinding()] param()
            }
            class Cache {
              [string] Get([string]$k) { return $k }
            }
            """))
        self.assertEqual(symbols["Get-Thing"].doc, "Returns things.")
        self.assertEqual(symbols["Cache"].kind, "class")
        self.assertEqual(symbols["Get"].parent, "Cache")

    def test_r_functions_roxygen_and_classes(self):
        symbols = by_name(extract("clean.R", """
            #' Clean the data.
            #' @param df a frame
            clean_data <- function(df) {
              df
            }
            .hidden <- function() NULL
            setClass("Person", representation(name = "character"))
            """))
        self.assertEqual(symbols["clean_data"].doc, "Clean the data.")
        self.assertFalse(symbols[".hidden"].exported)
        self.assertEqual(symbols["Person"].kind, "class")


class LinearTimeTest(unittest.TestCase):
    """Declaration patterns run over every line, so none may backtrack superlinearly.

    The bound is generous so a slow runner never flakes: each input took seconds, some
    minutes, while a pattern could split one run of spaces or parentheses many ways.
    """

    def extract_quickly(self, path, text):
        start = time.perf_counter()
        result = project_symbols.extract(path, text)
        self.assertLess(time.perf_counter() - start, 1.0, f"{path} took too long")
        return result

    def test_an_asset_inlined_in_a_template_literal(self):
        # The lexer blanks the literal, which leaves one long line of spaces.
        asset = "iVBORw0KGgoAAAANSUhEUgAA" * 850
        result = self.extract_quickly("src/assets/logo.ts", "export const logo = `\n" + asset +
                                      "\n`;\n\nexport function useLogo() {\n  return logo;\n}\n")
        self.assertEqual([symbol.name for symbol in result.symbols], ["useLogo"])

    def test_long_runs_after_a_keyword_or_a_name(self):
        blank = " " * 20000
        cases = [
            ("src/a.ts", f"function{blank}\n  handler{blank}\nmodule.exports = function{blank}\n"),
            ("src/a.php", f"<?php\nfunction {blank}\nnamespace{blank}{blank}{blank}x\n"),
            ("src/a.go", f"package a\nfunc ({blank}\n"),
            ("src/a.rs", f"impl{blank[:2000]}\n"),
            ("src/A.kt", f"fun{blank}{blank}x\n"),
            ("src/A.java", "class A {\n  A" + "b" * 20000 + "\n}\n"),
            ("src/A.cs", "class A {\n  A" + "b" * 20000 + "\n}\n"),
            ("src/a.cpp", f"namespace{blank}{blank}\nFoo::bar(x){blank}{blank}\n"),
            ("src/words.h", "class Words {\n" + "  word\n" * 8000 + "};\n" + "word\n" * 8000),
            ("src/words.c", "word\n" * 8000),
            ("src/static.c", "static\n" * 4000),
            ("src/inline.cpp", "inline\n" * 4000),
        ]
        for path, text in cases:
            with self.subTest(path=path):
                self.extract_quickly(path, text)

    def test_gnu_style_keeps_static_above_the_return_type(self):
        result = self.extract_quickly(
            "src/list.c", "static\nint\nlist_grow(struct list *l)\n{\n    return 0;\n}\n")
        [symbol] = result.symbols
        self.assertEqual((symbol.name, symbol.exported), ("list_grow", False))

    def test_a_macro_table_without_a_body(self):
        table = "".join(f'ERROR_CODE(E_{n}, {n}, "message {n}")\n' for n in range(1000))
        self.assertEqual(self.extract_quickly("src/errors.h", table).symbols, [])
        self.assertEqual(self.extract_quickly("src/errors.c", table * 5).symbols, [])


class DispatchTest(unittest.TestCase):
    def test_unknown_extensions_are_not_extracted(self):
        self.assertIsNone(project_symbols.extract("notes.txt", "hello"))
        self.assertIsNone(project_symbols.language_of("image.png"))
        self.assertEqual(project_symbols.language_of("src/App.TSX"), "typescript")


class DeclarationsTest(unittest.TestCase):
    def as_rows(self, file_symbols):
        return [(item.name, item.kind, item.line, item.owner) for item in file_symbols.declarations]

    def test_a_python_file_declares_its_parameters_and_variables_from_the_same_parse(self):
        result = extract("orders.py", """
            class Encoder(json.JSONEncoder):
                def default(self, o):
                    text = str(o)
                    return text
            """)
        self.assertEqual(self.as_rows(result), [("self", "parameter", 2, "Encoder"),
                                               ("o", "parameter", 2, "Encoder"),
                                               ("text", "variable", 3, None)])

    def test_a_script_declares_its_variables_and_named_functions_parameters(self):
        result = extract("orders.ts", """
            export function total(lines: number[]) {
              const subtotal = 0;
            }
            """)
        self.assertEqual(self.as_rows(result), [("lines", "parameter", 1, None),
                                               ("subtotal", "variable", 2, None)])

    def test_other_languages_declare_no_variables(self):
        self.assertEqual(extract("Orders.java", "public class Orders { int count = 0; }\n").declarations, ())


if __name__ == "__main__":
    unittest.main()
