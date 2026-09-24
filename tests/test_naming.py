"""Naming findings: names that are vague, encoded, numbered, noisy, verb-like, too short,
unconventional, or unrelated to their file."""

import tempfile
import textwrap
import unittest
from pathlib import Path

import support  # noqa: F401  (puts the scripts folder on sys.path)
import map_structure
import symbols as project_symbols
from source import files as project_files
from structure import naming as structure_naming
from structure import report as structure_report
from structure import roles as structure_roles

NO_ROLES = structure_roles.Roles([])

CSHARP_MAIN = """
    public class Program
    {
        public static void main() {}
    }
    """


def roles_with(*lines):
    """Only the given clean-roles statements, as a project's .clean/roles.md declares them."""
    return structure_roles.Roles(structure_roles.parse_roles(
        "```clean-roles\n" + "\n".join(lines) + "\n```\n", "roles.md"))


def naming_findings(files, roles=NO_ROLES, project_roots=()):
    """The naming findings for files, a path -> source mapping."""
    roled_files = []
    texts = {}
    for path, source in files.items():
        text = textwrap.dedent(source).lstrip("\n")
        roled_files.append(structure_roles.assign(
            project_symbols.extract(path, text), roles, project_files.is_test_path(path)))
        texts[path] = text
    return structure_naming.find_names(roled_files, roles, texts, project_roots)


def findings_for(files, roles=NO_ROLES, project_roots=()):
    """The naming findings for files as (rule, name, kind) triples."""
    return {(item["rule"], item["name"], item["kind"])
            for item in naming_findings(files, roles, project_roots)}


def names_in(path, source, roles=NO_ROLES):
    """The naming findings for one file as (rule, name, kind) triples."""
    return findings_for({path: source}, roles)


def map_of(files):
    """The structure map of a throwaway project holding files."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for path, text in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return map_structure.build_map(root, packs=[], depth=2)


class VagueTest(unittest.TestCase):
    def test_a_bare_verb_function_and_generic_data_names_are_vague(self):
        self.assertEqual(names_in("src/orders.py", "def process(data): tmp = data; return tmp\n"),
                         {("vague", "process", "function"), ("vague", "data", "parameter"),
                          ("vague", "tmp", "variable")})

    def test_intent_revealing_names_pass(self):
        self.assertEqual(names_in("src/invoices.py",
                                  "def calculate_invoice_total(order): subtotal = sum(order.lines)\n"),
                         set())

    def test_a_method_takes_its_object_from_its_class(self):
        self.assertEqual(names_in("src/pipeline.py", """
            class OrderPipeline:
                def process(self, order):
                    return order
            """), set())

    def test_a_handlers_res_parameter_is_dictated_but_a_res_variable_is_vague(self):
        self.assertEqual(names_in("src/users.js", """
            function listUsers(req, res, next) {}
            async function loadUsers() {
              const res = await fetch("/users");
            }
            """), {("vague", "res", "variable")})

    def test_a_vague_word_naming_one_of_the_projects_types_is_its_vocabulary(self):
        self.assertEqual(findings_for({
            "app/models/item.py": "class Item:\n    pass\n",
            "app/routers/items.py": "def read_item(item_id):\n    item = load(item_id)\n    return item\n",
        }), set())

    def test_a_types_vocabulary_stays_inside_its_own_project(self):
        self.assertEqual(findings_for({
            "shop/app/models.py": "class Item:\n    pass\n",
            "shop/app/views.py": "def show(item_id):\n    item = load(item_id)\n",
            "tools/report.py": "def render(item):\n    return item\n",
        }, project_roots=("shop",)), {("vague", "item", "parameter")})

    def test_the_data_form_of_a_bare_verb_is_vague(self):
        self.assertEqual(names_in("src/rows.js", "function handleData(rows) {}\n"),
                         {("vague", "handleData", "function")})

    def test_a_name_bound_again_in_its_scope_is_reported_once_where_first_bound(self):
        found = naming_findings({"src/totals.py": """
            def total(tmp):
                tmp = clean(tmp)
                obj = 0
                obj = sum(tmp)
                return obj
            """})
        self.assertEqual([(item["name"], item["kind"], item["line"]) for item in found],
                         [("tmp", "parameter", 1), ("obj", "variable", 3)])


class EncodedTest(unittest.TestCase):
    def test_a_type_prefix_or_an_interface_I_outside_dotnet_and_com_is_encoded(self):
        self.assertEqual(names_in("src/user.ts", """
            const strName = "";
            let iCount = 0;
            interface IUser {}
            """), {("encoded", "strName", "variable"), ("encoded", "iCount", "variable"),
                   ("encoded", "IUser", "class")})
        self.assertEqual(names_in("src/IUser.cs", "interface IUser {}\n"), set())
        self.assertEqual(names_in("src/renderer.hpp",
                                  "class IRenderer {\npublic:\n    virtual void draw() = 0;\n};\n"), set())

    def test_a_type_or_scope_prefix_is_encoded_but_a_snake_case_owner_is_not(self):
        self.assertEqual(names_in("src/frame.js", """
            function show(sTitle) {
              const m_count = 0;
              const _iTotal = 0;
              const iFrame = document.createElement("iframe");
              const obj_type = typeof sTitle;
            }
            """), {("encoded", "sTitle", "parameter"), ("encoded", "m_count", "variable"),
                   ("encoded", "_iTotal", "variable")})

    def test_a_project_that_prefixes_most_interfaces_with_I_has_chosen_the_prefix(self):
        entities = ("User", "Order", "Cart", "Invoice", "Payment", "Address", "Country", "Browser",
                    "Session", "Role")
        prefixed = "".join(f"export interface I{entity} {{}}\n" for entity in entities)
        self.assertEqual(names_in("src/interfaces.ts", prefixed + "export interface Settings {}\n"), set())
        unprefixed = "".join(f"export interface {entity} {{}}\n" for entity in entities)
        self.assertEqual(names_in("src/interfaces.ts", unprefixed + "export interface ISettings {}\n"),
                         {("encoded", "ISettings", "class")})


class NumberedTest(unittest.TestCase):
    def test_copies_told_apart_by_a_number_or_a_suffix_are_numbered(self):
        self.assertEqual(findings_for({
            "src/users.js": "function getUser2() {}\nclass UserNew {}\n",
            "src/handlers.py": "def handler_v2(): ...\n",
        }), {("numbered", "getUser2", "function"), ("numbered", "UserNew", "class"),
             ("numbered", "handler_v2", "function")})

    def test_a_function_copy_is_numbered_but_a_predicate_a_copy_operation_or_a_year_is_not(self):
        self.assertEqual(names_in("src/orders.py", """
            def process_order_new(order): ...
            def is_new(order): ...
            def deep_copy(order): ...
            tax_rules_2024 = {}
            """), {("numbered", "process_order_new", "function")})

    def test_digits_in_a_term_or_a_value_are_no_copy_number(self):
        self.assertEqual(names_in("src/codec.py", """
            def sha256_digest(payload): ...
            def to_utf8(text): ...
            def decode_base64(encoded): ...
            def md5(content): ...
            def as_int32(number): ...
            def to_float64(number): ...
            def line_length(x1, y1, x2, y2): ...
            def log10(value): ...
            def format_rfc3339(moment): ...
            def warn_when_sum_is_not_100(total): ...
            api_v1 = object()
            requires_zip64 = True
            request_uuid4 = uuid4()
            b64 = encode(payload)
            is_pep8 = check(source)
            """), set())


class ClassNameTest(unittest.TestCase):
    def test_a_noise_word_ending_a_class_name_is_flagged(self):
        self.assertEqual(names_in("src/models.py", """
            class OrderManager: pass
            class UserInfo: pass
            class StringUtils: pass
            """), {("noise-word", "OrderManager", "class"), ("noise-word", "UserInfo", "class"),
                   ("noise-word", "StringUtils", "class")})

    def test_a_class_named_like_an_action_is_a_verb_class(self):
        self.assertEqual(names_in("src/orders.py", """
            class ProcessOrder: pass
            class OrderProcessor: pass
            """), {("verb-class", "ProcessOrder", "class"), ("noise-word", "OrderProcessor", "class")})

    def test_framework_terms_and_names_ending_in_a_role_noun_pass(self):
        self.assertEqual(names_in("shop/managers.py", """
            class ArticleManager(models.Manager): pass
            class ZoneInfo(tzinfo): pass
            class TimerContextManager: pass
            class CreateOrderCommand: pass
            class SendWelcomeEmailJob: pass
            class CreateOrder(Command): pass
            class ProcessPoolExecutor: pass
            class GetPassWarning(UserWarning): pass
            """), set())

    def test_a_class_named_for_the_interface_it_implements_takes_its_name(self):
        declaration = "public abstract class NotifyPropertyChanged : INotifyPropertyChanged\n{\n}\n"
        self.assertEqual(names_in("src/NotifyPropertyChanged.cs", declaration), set())

    def test_bases_listed_past_the_declarations_first_lines_still_count(self):
        self.assertEqual(names_in("shop/sessions.py", """
            class AsyncSessionManager(
                SessionBase,
                AbstractAsyncContextManager,
                Decorator,
            ):
                pass
            """), set())


class TooShortTest(unittest.TestCase):
    def test_loops_catches_lambdas_and_math_idioms_may_be_short(self):
        self.assertEqual(names_in("src/loops.py", """
            for i in range(3):
                pass
            try:
                pass
            except ValueError as e:
                pass
            square = lambda x: x
            id = 3
            with open("orders.csv") as f:
                pass
            _, extension = split("orders.csv")
            """), set())

    def test_other_names_under_three_characters_are_too_short(self):
        self.assertEqual(names_in("src/sums.py", "def f(a, b):\n    return a + b\n"),
                         {("too-short", "f", "function"), ("too-short", "a", "parameter"),
                          ("too-short", "b", "parameter")})

    def test_short_words_and_handles_every_reader_knows_pass(self):
        self.assertEqual(names_in("src/report.py", """
            df = read_sales()
            fig, ax = subplots()
            db = connect()
            fd = open_descriptor()
            it = iter(df)
            def on(event, pk):
                return event
            def search(rows, lo, hi, **kw): ...
            def report(tb): ...
            def localize(moment, tz): ...
            """), set())
        self.assertEqual(names_in("src/permissions.ts", "export const permission = {\n"
                                                        "  mounted(el: HTMLElement) {},\n};\n"), set())

    def test_class_attributes_are_fields_not_variables(self):
        self.assertEqual(names_in("src/orders.py", """
            class Order(models.Model):
                data = models.JSONField()
            """), set())

    def test_an_uppercase_name_is_a_type_variable_or_an_acronym(self):
        self.assertEqual(names_in("src/syntax.py", 'R = TypeVar("R")\n_JS = Syntax("javascript")\n'), set())


class ScriptDeclarationTest(unittest.TestCase):
    def test_parameters_of_named_functions_and_methods_are_judged(self):
        self.assertEqual(names_in("src/pick.ts", """
            export function pick<T>(obj: T, k: string) { return obj; }
            export const scale = (value: number, f: number): number => value * f;
            export const wrap = <T,>(tmp: T) => tmp;
            export const first = o => o;
            class Cart {
              add<T>(item: T) {}
            }
            """), {("vague", "obj", "parameter"), ("too-short", "f", "parameter"),
                   ("vague", "tmp", "parameter"), ("too-short", "o", "parameter"),
                   ("vague", "item", "parameter")})

    def test_parameter_properties_and_decorators_are_passed_over_to_the_name(self):
        self.assertEqual(names_in("src/orders.service.ts", """
            export class OrdersService {
              constructor(private readonly tmp: Store, @Inject(TOKEN) obj: Config) {}
            }
            """), {("vague", "tmp", "parameter"), ("vague", "obj", "parameter")})

    def test_parameter_names_inside_a_type_are_not_parameters(self):
        self.assertEqual(names_in("src/compare.ts",
                                  "export type Compare = (a: number, b: number) => number;\n"), set())

    def test_a_type_annotation_or_jsx_text_holds_no_declarator(self):
        self.assertEqual(names_in("src/cache.ts", "let lookup: Map<string, number> = new Map(), tmp = 0;\n"),
                         {("vague", "tmp", "variable")})
        self.assertEqual(names_in("src/Loading.jsx", "const view = <p>Loading, obj</p>;\n"), set())

    def test_a_function_assigned_to_a_constant_is_one_function(self):
        self.assertEqual(names_in("src/users.js", "export const getUser2 = () => {};\n"),
                         {("numbered", "getUser2", "function")})

    def test_every_declarator_of_a_declaration_is_judged(self):
        self.assertEqual(names_in("src/totals.js", "let tmp = 0, total = 0, obj;\n"),
                         {("vague", "tmp", "variable"), ("vague", "obj", "variable")})

    def test_a_renamed_or_positional_binding_is_the_authors_choice(self):
        self.assertEqual(names_in("src/view.js", """
            const { data: tmp } = response;
            const [obj, setObj] = useState();
            """), {("vague", "tmp", "variable"), ("vague", "obj", "variable")})

    def test_short_lived_and_dictated_names_are_not_judged(self):
        self.assertEqual(names_in("src/list.js", """
            const fs = require("fs");
            const { data, t } = useQuery();
            const ids = items.map((x) => x.id).filter(function (v) { return v; });
            items.forEach(o => o.id);
            render(obj);
            for (let i = 0; i < ids.length; i++) {}
            for (const item of ids) {}
            if (tmp) { load(); }
            try { load(); } catch (err) {}
            """), set())


class ConventionTest(unittest.TestCase):
    def test_casing_follows_each_languages_convention(self):
        self.assertEqual(names_in("src/users.py", "def getUser():\n    pass\n"),
                         {("convention", "getUser", "function")})
        self.assertEqual(names_in("src/users.js", "function get_user() {}\n"),
                         {("convention", "get_user", "function")})
        csharp = "public class Users\n{\n    public void getUser() {}\n}\n"
        self.assertEqual(names_in("src/Users.cs", csharp), {("convention", "getUser", "method")})
        self.assertEqual(names_in("src/users.go", "package users\n\nfunc getUser() {}\n"), set())
        self.assertEqual(names_in("src/users.rs", "pub fn loadUser() {}\n"),
                         {("convention", "loadUser", "function")})
        self.assertEqual(names_in("lib/users.rb", "class Users\n  def loadUser\n  end\nend\n"),
                         {("convention", "loadUser", "method")})
        java = "public class Users {\n    public void LoadUser() {}\n}\n"
        self.assertEqual(names_in("src/Users.java", java), {("convention", "LoadUser", "method")})

    def test_components_and_factories_may_be_pascal_case(self):
        self.assertEqual(names_in("src/UserCard.jsx", "export function UserCard() { return null; }\n"),
                         set())
        self.assertEqual(names_in("app/Greeting.kt", "@Composable\nfun Greeting(name: String) {}\n"), set())

    def test_names_a_framework_dictates_keep_its_casing(self):
        self.assertEqual(names_in("src/visitor.py", """
            class Collector(ast.NodeVisitor):
                def visit_FunctionDef(self, node): pass
                def __eq__(self, other): pass
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self): pass
            """), set())
        self.assertEqual(names_in("src/route.ts", "export async function GET(request: Request) {}\n"), set())
        self.assertEqual(names_in("src/UserService.java", """
            public class UserService {
                public UserService() {}
            }
            """), set())
        self.assertEqual(names_in("src/OrderForm.cs", """
            public partial class OrderForm : Form
            {
                private void btnSave_Click(object sender, EventArgs e) {}
            }
            """), set())

    def test_the_projects_majority_casing_wins_over_the_language_default(self):
        snake_methods = ("add_menu_page", "register_settings", "enqueue_scripts", "render_page",
                         "save_options", "load_textdomain", "add_meta_boxes", "sanitize_input",
                         "print_notices", "verify_nonce", "update_option")
        wordpress = ("<?php\nclass Plugin_Admin {\n"
                     + "".join(f"    public function {name}() {{}}\n" for name in snake_methods)
                     + "    public function renderSettings() {}\n}\n")
        self.assertEqual(names_in("src/class-plugin-admin.php", wordpress),
                         {("convention", "renderSettings", "method")})
        # Below the threshold the language default holds: PSR-1 camelCase methods.
        few = ("<?php\nclass Plugin_Admin {\n    public function add_menu_page() {}\n"
               "    public function renderSettings() {}\n}\n")
        self.assertEqual(names_in("src/class-plugin-admin.php", few),
                         {("convention", "add_menu_page", "method")})

    def test_each_project_of_a_monorepo_keeps_its_own_majority(self):
        snake_methods = "".join(f"    public function {verb}_{noun}() {{}}\n" for verb, noun in (
            ("add", "page"), ("save", "options"), ("load", "domain"), ("print", "notices"),
            ("verify", "nonce"), ("render", "page"), ("enqueue", "scripts"), ("register", "hooks"),
            ("sanitize", "input"), ("update", "option")))
        found = naming_findings({
            "blog/class-plugin.php": f"<?php\nclass Plugin {{\n{snake_methods}}}\n",
            "shop/app/Cart.php": "<?php\nclass Cart {\n    public function addItem() {}\n"
                                 "    public function remove_item() {}\n}\n",
        }, project_roots=("blog", "shop"))
        self.assertEqual([(item["name"], item["path"]) for item in found],
                         [("remove_item", "shop/app/Cart.php")])


class FileMismatchTest(unittest.TestCase):
    def test_a_file_named_for_another_type_in_a_one_type_per_file_language(self):
        self.assertEqual(names_in("src/UserService.java", "public class AccountRepository {}\n"),
                         {("file-mismatch", "AccountRepository", "file")})
        self.assertEqual(names_in("src/user_service.py", "class AccountRepository:\n    pass\n"), set())

    def test_a_file_named_for_its_type_and_a_qualifier_matches(self):
        self.assertEqual(findings_for({
            "src/MetaFieldTypes.cs": "public enum MetaFieldType { Text }\n",
            "src/IValidationComparer_T.cs": "public interface IValidationComparer<T> {}\n",
            "src/MailAdress.cs": "public class MailAddress {}\n",
        }), {("file-mismatch", "MailAddress", "file")})

    def test_an_entry_point_holds_what_its_template_puts_there(self):
        self.assertEqual(names_in("src/Program.cs", "var app = WebApplication.Create(args);\napp.Run();\n\n"
                                                    "public record WeatherForecast(int TemperatureC);\n"),
                         set())


class ExemptionTest(unittest.TestCase):
    def test_a_test_file_is_exempt(self):
        self.assertEqual(names_in("tests/test_orders.py", "def f(): pass\n"), set())

    def test_a_generated_file_is_exempt(self):
        data = map_of({"src/client.py": "# Code generated by protoc-gen-python. DO NOT EDIT.\n\n"
                                        "def f(): pass\n"})
        self.assertEqual(data["findings"]["names"], [])

    def test_an_ignored_name_is_exempt(self):
        self.assertEqual(names_in("src/Program.cs", CSHARP_MAIN), {("convention", "main", "method")})
        self.assertEqual(names_in("src/Program.cs", CSHARP_MAIN, roles_with("ignore-name = ^main$")),
                         set())

    def test_an_accepted_symbol_is_exempt(self):
        self.assertEqual(names_in("src/orders.py", "def process(order): pass\n",
                                  roles_with("accept src/orders.py = process")), set())


class NamesReportTest(unittest.TestCase):
    def test_the_map_reports_names_and_structure_md_lists_them_under_findings(self):
        data = map_of({"src/orders.py": "def load_orders():\n    data = []\n    return data\n"})
        self.assertEqual(data["findings"]["names"], [{
            "rule": "vague", "name": "data", "kind": "variable", "path": "src/orders.py", "line": 2,
            "cites": "N1",
        }])
        findings = structure_report.render_markdown(data).split("## Findings", 1)[1].split("## Tree")[0]
        self.assertIn("| Names | 1 |", findings)
        self.assertIn("### Names\n\n- vague (N1): 1 — `data` (`src/orders.py:2`)", findings)
        self.assertIn("cycles 0, names 1", structure_report.render_summary(data))

    def test_each_rule_lists_at_most_five_examples_within_top(self):
        source = "".join(f"def load_{letter}():\n    data = []\n    return data\n" for letter in "abcdefg")
        data = map_of({"src/orders.py": source})
        self.assertEqual(len(data["findings"]["names"]), 7)

        def vague_line(top):
            markdown = structure_report.render_markdown(data, top)
            return next(line for line in markdown.split("\n") if line.startswith("- vague (N1): 7"))

        self.assertEqual(vague_line(25).count("`data`"), 5)
        self.assertTrue(vague_line(25).endswith(", ..."))
        self.assertEqual(vague_line(2).count("`data`"), 2)


if __name__ == "__main__":
    unittest.main()
