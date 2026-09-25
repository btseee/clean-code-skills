"""Organization findings: file families, junk drawers, flat folders, unreferenced and
comment-heavy files, the move plan, and `map_structure.py --changed`."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

import support  # noqa: F401  (puts the scripts folder on sys.path)
import map_structure
import structure as structure_package
import symbols as project_symbols
from source import files as project_files
from structure import findings as structure_findings
from structure import organization as structure_organization
from structure import report as structure_report
from structure import roles as structure_roles

NO_ROLES = structure_roles.Roles([])
BILLING = ("src/billing_invoice.py", "src/billing_tax.py", "src/billing_export.py")
BILLING_IMPORTS = {"src/billing_invoice.py": ["src/billing_tax.py"],
                   "src/billing_tax.py": ["src/billing_export.py"],
                   "src/billing_export.py": ["src/billing_invoice.py"]}
TRACED = structure_organization.REFERENCE_TRACED_LANGUAGES


def roles_with(*lines):
    """Only the given clean-roles statements, as a project's .clean/roles.md declares them."""
    return structure_roles.Roles(structure_roles.parse_roles(
        "```clean-roles\n" + "\n".join(lines) + "\n```\n", "roles.md"))


def roled_files(files, roles=NO_ROLES):
    """Roled files for a path -> source mapping."""
    return [structure_roles.assign(project_symbols.extract(path, textwrap.dedent(source).lstrip("\n")),
                                   roles, project_files.is_test_path(path))
            for path, source in files.items()]


def write_files(root: Path, files: dict) -> None:
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def map_of(files, packs=()):
    """The structure map of a throwaway project holding files."""
    with tempfile.TemporaryDirectory() as directory:
        write_files(Path(directory), files)
        return map_structure.build_map(Path(directory), packs=list(packs), depth=2)


def script(comment_lines, code_lines, comment="// why this matters", code="const total = 1;"):
    return "".join(f"{comment}\n" for _ in range(comment_lines)) + \
        "".join(f"{code}\n" for _ in range(code_lines))


def run_map(*argv):
    """(exit code, stdout, stderr) of map_structure's main."""
    output, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        code = map_structure.main(list(argv))
    return code, output.getvalue(), errors.getvalue()


class FamilyTest(unittest.TestCase):
    def test_three_files_sharing_a_token_and_importing_each_other_are_a_family(self):
        self.assertEqual(structure_organization.find_families(BILLING_IMPORTS, BILLING), [{
            "folder": "src", "token": "billing", "files": sorted(BILLING), "suggestion": "src/billing/",
        }])

    def test_files_sharing_a_token_that_import_nothing_of_each_other_are_no_family(self):
        self.assertEqual(structure_organization.find_families({}, BILLING), [])

    def test_two_files_are_no_family(self):
        self.assertEqual(structure_organization.FAMILY_MINIMUM, 3)
        imports = {"src/billing_invoice.py": ["src/billing_tax.py"]}
        self.assertEqual(structure_organization.find_families(imports, BILLING[:2]), [])

    def test_the_family_is_the_files_one_import_graph_connects(self):
        # A chain connects all three; two pairs connect no three; an isolated file stays out.
        chain = {"src/billing_invoice.py": ["src/billing_tax.py"],
                 "src/billing_export.py": ["src/billing_tax.py"]}
        paths = BILLING + ("src/billing_notes.py",)
        self.assertEqual(structure_organization.find_families(chain, paths)[0]["files"], sorted(BILLING))
        pairs = {"src/billing_invoice.py": ["src/billing_tax.py"],
                 "src/billing_export.py": ["src/billing_notes.py"]}
        self.assertEqual(structure_organization.find_families(pairs, paths), [])

    def test_a_family_named_like_its_folder_is_not_proposed(self):
        inside = {path.replace("src/", "src/billing/"): [target.replace("src/", "src/billing/")
                                                          for target in targets]
                  for path, targets in BILLING_IMPORTS.items()}
        self.assertEqual(structure_organization.find_families(inside, list(inside)), [])
        users = {"src/users/user_model.py": ["src/users/user_store.py"],
                 "src/users/user_store.py": ["src/users/user_api.py"]}
        self.assertEqual(structure_organization.find_families(
            users, list(users) + ["src/users/user_api.py"]), [])

    def test_a_folder_whose_compound_or_dotted_name_holds_the_token_already_names_it(self):
        compound = ("BusinessProcessContext.cs", "BusinessProcessSession.cs", "BusinessProcessAttribute.cs")
        dotted = ("IService.cs", "ServiceItem.cs", "ServiceAttribute.cs")
        for folder, names in (("Exchange/BusinessProcess", compound), ("Inklusit.Core.Service", dotted)):
            paths = [f"{folder}/{name}" for name in names]
            imports = {paths[0]: [paths[1]], paths[1]: [paths[2]]}
            self.assertEqual(structure_organization.find_families(imports, paths), [], folder)

    def test_the_suggestion_keeps_the_casing_of_the_file_names(self):
        imports = {"src/BillingInvoice.cs": ["src/BillingTax.cs"],
                   "src/BillingTax.cs": ["src/BillingExport.cs"]}
        paths = ["src/BillingInvoice.cs", "src/BillingTax.cs", "src/BillingExport.cs"]
        self.assertEqual(structure_organization.find_families(imports, paths)[0]["suggestion"],
                         "src/Billing/")

    def test_a_jvm_family_folder_is_a_lowercase_package(self):
        package = "src/main/java/com/acme/shop"
        paths = [f"{package}/Billing{name}.java" for name in ("Invoice", "Tax", "Export")]
        imports = {paths[0]: [paths[1]], paths[1]: [paths[2]]}
        self.assertEqual(structure_organization.find_families(imports, paths)[0]["suggestion"], f"{package}/billing/")
        kotlin = [path.replace(".java", ".kt") for path in paths]
        self.assertEqual(structure_organization.find_families({kotlin[0]: kotlin[1:]}, kotlin)[0]["suggestion"],
                         f"{package}/billing/")
        php = [f"src/Billing{name}.php" for name in ("Invoice", "Tax", "Export")]
        self.assertEqual(structure_organization.find_families({php[0]: php[1:]}, php)[0]["suggestion"],
                         "src/Billing/")

    def test_prefixes_that_name_no_concept_make_no_family(self):
        for names in (("IOrderService.cs", "IUserService.cs", "IPaymentService.cs"),
                      ("app.module.ts", "app.controller.ts", "app.service.ts"),
                      ("useAuth.ts", "useCart.ts", "useUser.ts")):
            paths = [f"src/{name}" for name in names]
            imports = {paths[0]: [paths[1]], paths[1]: [paths[2]]}
            self.assertEqual(structure_organization.find_families(imports, paths), [], names)

    def test_a_header_and_its_source_are_one_file_of_a_family(self):
        paths = ["Sources/FeedItem.h", "Sources/FeedItem.m", "Sources/FeedStore.h", "Sources/FeedStore.m"]
        imports = {"Sources/FeedItem.m": ["Sources/FeedItem.h"], "Sources/FeedStore.h": ["Sources/FeedItem.h"],
                   "Sources/FeedStore.m": ["Sources/FeedStore.h"]}
        self.assertEqual(structure_organization.find_families(imports, paths), [])
        imports["Sources/FeedCache.h"] = ["Sources/FeedStore.h"]
        self.assertEqual(len(structure_organization.find_families(imports, paths + ["Sources/FeedCache.h"])), 1)

    def test_tests_do_not_count(self):
        paths = ["src/billing_invoice.py", "src/billing_tax.py", "src/test_billing.py"]
        imports = {paths[0]: [paths[1]], paths[2]: [paths[0]]}
        self.assertEqual(structure_organization.find_families(imports, paths), [])


class JunkDrawerTest(unittest.TestCase):
    ROLES = roles_with("role service = **/services/**", "name service = Service$",
                       "name repository = Repository$")
    FILES = {
        "src/utils/billing.py": "class BillingService:\n    pass\n",
        "src/utils/storage.py": "class InvoiceRepository:\n    pass\n",
    }

    def test_a_utils_folder_holding_several_roles_is_split_by_role(self):
        files = roled_files(self.FILES, self.ROLES)
        self.assertEqual(structure_organization.find_junk_drawers(files, []), [{
            "folder": "src/utils",
            "splits": [
                {"by": "role", "name": "repository", "files": ["src/utils/storage.py"], "to": None},
                {"by": "role", "name": "service", "files": ["src/utils/billing.py"], "to": None},
            ],
            "rename": None,
        }])

    def test_files_sharing_a_name_group_by_it_and_the_rest_wait_for_a_name(self):
        files = roled_files({"src/utils/date_format.py": "def show(day):\n    return day\n",
                             "src/utils/date_parse.py": "def read(text):\n    return text\n",
                             "src/utils/slugify.py": "def slug(text):\n    return text\n"})
        self.assertEqual(structure_organization.find_junk_drawers(files, [])[0]["splits"], [
            {"by": "name", "name": "date", "files": ["src/utils/date_format.py", "src/utils/date_parse.py"],
             "to": None},
            {"by": "unsorted", "name": None, "files": ["src/utils/slugify.py"], "to": None},
        ])

    def test_a_junk_drawer_of_one_concept_is_renamed_for_it(self):
        files = roled_files({"src/helpers/date_format.py": "def show(day):\n    return day\n",
                             "src/helpers/date_parse.py": "def read(text):\n    return text\n"})
        self.assertEqual(structure_organization.find_junk_drawers(files, [])[0]["rename"], "src/date/")
        roles = roles_with("name repository = Repository$")
        files = roled_files({"src/common/orders.py": "class OrderRepository:\n    pass\n",
                             "src/common/users.py": "class UserRepository:\n    pass\n"}, roles)
        self.assertEqual(structure_organization.find_junk_drawers(files, [])[0]["rename"], "src/repositories/")

    def test_one_role_moves_to_its_home_rather_than_renaming(self):
        files = roled_files({"src/misc/orders.py": "class OrderService:\n    pass\n",
                             "src/misc/users.py": "class UserService:\n    pass\n",
                             "src/services/billing.py": "class BillingService:\n    pass\n"}, self.ROLES)
        drawer = structure_organization.find_junk_drawers(files, [])[0]
        self.assertEqual((drawer["rename"], drawer["splits"][0]["to"]), (None, "src/services/"))

    def test_a_drawer_inside_its_files_role_home_asks_for_a_name_not_a_move(self):
        roles = roles_with("role component = **/components/**")
        files = roled_files({"src/components/helper/LanguageSwitch.ts": "export class LanguageSwitch {}\n",
                             "src/components/helper/PermissionSelect.ts": "export class PermissionSelect {}\n",
                             "src/components/forms/Input.ts": "export class Input {}\n"}, roles)
        drawer = structure_organization.find_junk_drawers(files, [])[0]
        self.assertEqual((drawer["splits"][0]["by"], drawer["splits"][0]["to"], drawer["rename"]),
                         ("unsorted", None, None))

    def test_a_package_marker_is_no_file_of_the_drawer(self):
        files = roled_files({"src/tools/__init__.py": "", "src/tools/vault.py": "def read():\n    pass\n"})
        self.assertEqual(structure_organization.find_junk_drawers(files, []), [])

    def test_one_file_is_no_junk_drawer(self):
        files = roled_files({"src/utils/slugify.py": "def slug(text):\n    return text\n",
                             "src/utils/test_slugify.py": "def test_slug():\n    pass\n"})
        self.assertEqual(structure_organization.find_junk_drawers(files, []), [])

    def test_junk_drawers_and_misplaced_code_share_one_definition_of_a_home(self):
        files = roled_files(self.FILES, self.ROLES)
        with mock.patch.object(structure_findings, "home_folders", wraps=structure_findings.home_folders) as homes:
            structure_organization.find_junk_drawers(files, [])
        homes.assert_called_once()

    def test_a_split_goes_to_the_role_home_the_project_already_has(self):
        files = roled_files(dict(self.FILES, **{"src/services/orders.py": "class OrderService:\n    pass\n"}),
                            self.ROLES)
        found = structure_organization.find_junk_drawers(files, [])
        self.assertEqual({split["name"]: split["to"] for split in found[0]["splits"]},
                         {"repository": None, "service": "src/services/"})

    def test_a_folder_named_for_its_role_is_no_junk_drawer(self):
        files = roled_files({path.replace("utils", "services"): source for path, source in self.FILES.items()},
                            self.ROLES)
        self.assertEqual(structure_organization.find_junk_drawers(files, []), [])

    def test_role_less_files_are_listed_for_naming(self):
        files = roled_files({"src/helpers/billing.py": "class BillingService:\n    pass\n",
                             "src/helpers/text.py": "def pad(text):\n    return text\n"}, self.ROLES)
        self.assertEqual(structure_organization.find_junk_drawers(files, []), [{
            "folder": "src/helpers",
            "splits": [{"by": "role", "name": "service", "files": ["src/helpers/billing.py"], "to": None},
                       {"by": "unsorted", "name": None, "files": ["src/helpers/text.py"], "to": None}],
            "rename": None,
        }])

    def test_a_family_in_a_junk_drawer_moves_beside_it(self):
        family_paths = ["src/common/billing_invoice.py", "src/common/billing_tax.py",
                        "src/common/billing_export.py"]
        family = {"folder": "src/common", "token": "billing", "files": sorted(family_paths),
                  "suggestion": "src/common/billing/"}
        files = roled_files(dict({path: "def total():\n    return 1\n" for path in family_paths},
                                 **{"src/common/storage.py": "class InvoiceRepository:\n    pass\n"}),
                            self.ROLES)
        splits = structure_organization.find_junk_drawers(files, [family])[0]["splits"]
        self.assertIn({"by": "family", "name": "billing", "files": sorted(family_paths), "to": "src/billing/"},
                      splits)


class FlatFolderTest(unittest.TestCase):
    def test_more_than_fifteen_production_files_make_a_flat_folder(self):
        self.assertEqual(structure_organization.FLAT_FOLDER_LIMIT, 15)
        paths = [f"src/module_{index}.py" for index in range(16)]
        self.assertEqual(structure_organization.find_flat_folders(paths, []),
                         [{"folder": "src", "file_count": 16, "families": []}])

    def test_fifteen_files_are_not_flat(self):
        paths = [f"src/module_{index}.py" for index in range(15)]
        self.assertEqual(structure_organization.find_flat_folders(paths, []), [])

    def test_tests_do_not_count(self):
        paths = [f"src/module_{index}.py" for index in range(15)] + \
                [f"src/test_module_{index}.py" for index in range(5)]
        self.assertEqual(structure_organization.find_flat_folders(paths, []), [])

    def test_a_folder_whose_files_are_mostly_one_kind_is_not_flat(self):
        # Sixteen tokenizers, or API clients, are one concept: there is nothing to group them by.
        self.assertEqual(structure_organization.ONE_KIND_SHARE, 0.75)
        names = ("Date", "Time", "Year", "Regex", "Split", "Enum", "Bool", "Number", "Money", "Word", "Path",
                 "Guid")
        kinds = [f"Fulltext/Tokenizers/{name}Tokenizer.cs" for name in names]
        others = [f"Fulltext/Tokenizers/{name}.cs" for name in ("Quarter", "Settings", "Substitution", "Mode")]
        self.assertEqual(structure_organization.find_flat_folders(kinds + others, []), [])
        self.assertEqual(len(structure_organization.find_flat_folders(
            kinds[:11] + others + ["Fulltext/Tokenizers/Span.cs"], [])), 1)
        clients = [f"src/api/administration/{name.lower()}.api.ts"
                   for name in names + ("User", "Role", "Unit", "Zone")]
        self.assertEqual(structure_organization.find_flat_folders(clients, []), [])

    def test_a_folder_whose_files_mostly_share_one_role_is_not_flat(self):
        roles = roles_with("name service = Service$")
        sources = {f"src/{name.lower()}.py": f"class {name}Service:\n    pass\n" for name in (
            "Order", "User", "Invoice", "Refund", "Cart", "Stock", "Price", "Tax", "Ship", "Mail", "Audit", "Login")}
        sources.update({f"src/module_{index}.py": "def run():\n    pass\n" for index in range(4)})
        files = roled_files(sources, roles)
        self.assertEqual(structure_organization.find_flat_folders(list(sources), [], roled_files=files), [])
        del sources["src/login.py"]
        sources["src/module_4.py"] = "def run():\n    pass\n"
        files = roled_files(sources, roles)
        self.assertEqual(len(structure_organization.find_flat_folders(list(sources), [], roled_files=files)), 1)

    def test_a_flat_folder_names_the_families_to_group_it_by(self):
        family = {"folder": "src", "token": "billing", "files": sorted(BILLING), "suggestion": "src/billing/"}
        paths = [f"src/module_{index}.py" for index in range(13)] + list(BILLING)
        self.assertEqual(structure_organization.find_flat_folders(paths, [family])[0]["families"], ["billing"])


class UnreferencedTest(unittest.TestCase):
    ROLES = roles_with("role service = **/services/**")

    def unreferenced(self, files, imports=None, roles=None, **options):
        found = structure_organization.find_unreferenced(imports or {}, roled_files(files, roles or self.ROLES),
                                                         TRACED, **options)
        return [item["path"] for item in found]

    def test_a_file_nothing_imports_is_possibly_unused(self):
        files = {"src/main.py": "import billing\n", "src/billing.py": "def total():\n    return 1\n",
                 "src/orphan.py": "def forgotten():\n    return 1\n"}
        self.assertEqual(self.unreferenced(files, {"src/main.py": ["src/billing.py"]}), ["src/orphan.py"])

    def test_an_entry_point_is_not_unreferenced(self):
        self.assertEqual(self.unreferenced({"src/main.py": "print('hi')\n"}), [])

    def test_a_file_holding_a_role_is_not_unreferenced(self):
        self.assertEqual(self.unreferenced({"src/services/billing.py": "def total():\n    return 1\n"}), [])
        roles = roles_with("name command = Command$")
        self.assertEqual(self.unreferenced({"src/sync.py": "class SyncCommand:\n    pass\n"}, roles=roles), [])

    def test_a_language_whose_imports_the_map_cannot_trace_is_not_judged(self):
        self.assertNotIn("go", TRACED)
        self.assertEqual(self.unreferenced({"src/orphan.go": "package orphan\n\nfunc Forgotten() {}\n"}), [])

    def test_a_file_only_tests_import_is_referenced(self):
        files = {"src/orphan.py": "def forgotten():\n    return 1\n",
                 "tests/test_orphan.py": "from src.orphan import forgotten\n"}
        self.assertEqual(self.unreferenced(files, {"tests/test_orphan.py": ["src/orphan.py"]}), [])

    def test_a_program_is_not_unreferenced(self):
        files = {"src/cli.py": "def run():\n    pass\n", "scripts/release.py": "print('release')\n"}
        self.assertEqual(self.unreferenced(files, programs={"src/cli.py"}), [])
        self.assertTrue(structure_organization.runs_as_program(
            "def run():\n    pass\n\n\nif __name__ == \"__main__\":\n    run()\n"))
        self.assertTrue(structure_organization.runs_as_program("#!/usr/bin/env node\nrun();\n"))
        self.assertTrue(structure_organization.runs_as_program(
            "class Tool {\n  public static void main(String[] args) {}\n}\n"))
        self.assertFalse(structure_organization.runs_as_program("def run():\n    pass\n"))

    def test_an_app_shell_named_main_is_an_entry_point(self):
        files = {"android/app/src/main/kotlin/MainActivity.kt": "class MainActivity : FlutterActivity()\n",
                 "src/MainWindow.cs": "public class MainWindow {}\n"}
        self.assertEqual(self.unreferenced(files), [])

    def test_example_code_is_not_unreferenced(self):
        files = {"samples/processes/AddUserProcess.cs": "public class AddUserProcess {}\n",
                 "examples/quickstart.py": "print('hi')\n"}
        self.assertEqual(self.unreferenced(files), [])

    def test_a_file_a_tool_loads_by_name_is_not_unreferenced(self):
        files = {"vite.config.ts": "export default {};\n", "tests/conftest.py": "import pytest\n",
                 "setup.py": "from setuptools import setup\n", "src/env.d.ts": "declare const VERSION: string;\n",
                 "src/Button.stories.tsx": "export default { title: 'Button' };\n",
                 "src/Card.story.tsx": "export default { title: 'Card' };\n",
                 ".eslintrc.js": "module.exports = {};\n", "public/sw.js": "self.addEventListener('fetch', f);\n"}
        self.assertEqual(self.unreferenced(files), [])

    def test_an_imported_package_vouches_for_no_module_nobody_imports(self):
        # The resolver names the module `from billing import tax` imports; the package is no proxy.
        files = {"src/main.py": "from billing import tax\n", "src/billing/__init__.py": "",
                 "src/billing/tax.py": "def rate():\n    return 1\n"}
        self.assertEqual(self.unreferenced(files, {"src/main.py": ["src/billing/__init__.py"]}),
                         ["src/billing/tax.py"])

    def test_an_import_the_map_cannot_resolve_still_references_the_file_it_names(self):
        files = {"src/main.ts": "import Button from '@/widgets/Button';\nimport { rate } from 'billing';\n",
                 "src/widgets/Button.ts": "export const Button = 1;\n",
                 "src/billing/tax.py": "def rate():\n    return 1\n",
                 "src/app.py": "from billing import tax\n"}
        unresolved = {"src/main.ts": ["@/widgets/Button"], "src/app.py": ["billing"]}
        self.assertEqual(self.unreferenced(files, unresolved_imports=unresolved), [])

    def test_only_an_unresolved_import_of_a_project_name_in_the_same_language_counts(self):
        files = {"src/main.ts": "import debounce from 'lodash/debounce';\n",
                 "src/timing/debounce.ts": "export const debounce = 1;\n",
                 "app.py": "import logging\n", "web/logging/format.ts": "export const format = 1;\n"}
        unresolved = {"src/main.ts": ["lodash/debounce"], "app.py": ["logging"]}
        self.assertEqual(self.unreferenced(files, unresolved_imports=unresolved),
                         ["src/timing/debounce.ts", "web/logging/format.ts"])

    def test_a_file_an_entry_line_names_is_not_unreferenced(self):
        roles = roles_with("entry app/**/sitemap.*")
        self.assertEqual(self.unreferenced({"app/blog/sitemap.ts": "export default function sitemap() {}\n",
                                            "app/blog/unused.ts": "export const unused = 1;\n"}, roles=roles),
                         ["app/blog/unused.ts"])

    def test_an_annotated_or_framework_derived_class_is_reachable_by_its_framework(self):
        files = {
            "src/Billing.java": "@Service\npublic class Billing {}\n",
            "src/Report.java": "public class Report extends HttpServlet {}\n",
            "src/Users.cs": "[ApiController]\npublic class Users {}\n",
            "src/Sweeper.cs": "public sealed class Sweeper : BackgroundService {}\n",
            "src/Sync.php": "<?php\n#[AsCommand(name: 'sync')]\nclass Sync {}\n",
            "src/Mailer.php": "<?php\nclass Mailer extends Mailable {}\n",
            "src/Jobs.kt": "@Component\nclass Jobs {\n}\n",
            "src/Base.java": "public class Base<T> {}\n",
            "src/Orders.java": "public class Orders extends Base<Order> {}\n",
            "src/Order.java": "public class Order {}\n",
        }
        self.assertEqual(self.unreferenced(files, {"src/Orders.java": ["src/Base.java", "src/Order.java"]}),
                         ["src/Orders.java"])

    def test_only_a_scripts_folder_marks_programs_since_the_walk_never_enters_bin(self):
        self.assertIn("bin", project_files.SKIP_DIRS)
        self.assertEqual(structure_organization.PROGRAM_FOLDERS, frozenset({"scripts"}))

    def test_a_file_that_declares_no_type_is_not_judged_where_types_are_what_the_map_traces(self):
        files = {"src/Extensions.kt": "fun String.shout() = uppercase()\n",
                 "src/Orphan.java": "public class Orphan {}\n"}
        self.assertEqual(self.unreferenced(files), ["src/Orphan.java"])

    def test_a_partial_type_is_not_judged(self):
        # Its other half may live in markup or generated code the map does not read.
        self.assertEqual(self.unreferenced({"src/OrderForm.razor.cs": "public partial class OrderForm {}\n"}), [])


class CommentHeavyTest(unittest.TestCase):
    def heavy(self, text, path="src/prices.js", language="javascript"):
        return structure_organization.find_comment_heavy({path: text}, {path: language})

    def test_a_file_whose_comments_rival_its_code_is_comment_heavy(self):
        self.assertEqual(self.heavy(script(25, 20)), [{
            "path": "src/prices.js", "comment_lines": 25, "nonblank_lines": 45, "ratio": 0.56,
        }])

    def test_nineteen_comment_lines_are_too_few(self):
        self.assertEqual(structure_organization.COMMENT_MINIMUM, 20)
        self.assertEqual(self.heavy(script(19, 20)), [])

    def test_comments_must_be_at_least_forty_percent_of_the_lines(self):
        self.assertEqual(structure_organization.COMMENT_RATIO, 0.4)
        self.assertEqual(len(self.heavy(script(20, 30))), 1)
        self.assertEqual(self.heavy(script(20, 31)), [])

    def test_a_license_header_is_not_counted(self):
        header = "/*\n" + "".join(f" * Copyright 2026 Acme. Licensed under MIT, line {index}.\n"
                                  for index in range(23)) + " */\n"
        self.assertEqual(self.heavy(header + script(5, 20)), [])
        spdx = "# SPDX-License-Identifier: MIT\n" + "".join(f"# Licensed terms {index}.\n" for index in range(24))
        self.assertEqual(self.heavy(spdx + script(0, 20, code="total = 1"), "src/prices.py", "python"), [])

    def test_python_docstrings_are_not_comments(self):
        docstring = '"""Prices.\n\n' + "".join(f"Explains step {index}.\n" for index in range(30)) + '"""\n'
        self.assertEqual(self.heavy(docstring + script(0, 10, code="total = 1"), "src/prices.py", "python"), [])

    def test_api_doc_comments_are_documentation_like_a_docstring(self):
        xml_docs = "".join(f"/// <summary>Step {index}.</summary>\n" for index in range(25))
        code = script(0, 20, code="int total = 1;")
        self.assertEqual(self.heavy(xml_docs + code, "src/Prices.cs", "csharp"), [])
        javadoc = "/**\n" + "".join(f" * Step {index} explains itself.\n" for index in range(23)) + " */\n"
        self.assertEqual(self.heavy(javadoc + code, "src/Prices.java", "java"), [])

    def test_powershell_help_is_documentation(self):
        help_block = "<#\n.SYNOPSIS\n" + "".join(f"    Step {index}.\n" for index in range(24)) + "#>\n"
        code = script(0, 20, code="$total = 1")
        self.assertEqual(self.heavy(help_block + code, "Get-Report.ps1", "powershell"), [])

    def test_a_c_header_is_skipped_since_its_comments_document_its_api(self):
        self.assertEqual(self.heavy(script(25, 20, code="int total(void);"), "include/prices.h", "cpp"), [])
        self.assertEqual(len(self.heavy(script(25, 20, code="int total = 1;"), "src/prices.c", "c")), 1)

    def test_a_comment_after_code_is_code(self):
        self.assertEqual(self.heavy(script(0, 30, code="const total = 1; // why this matters")), [])

    def test_each_line_of_a_block_comment_counts(self):
        block = "/*\n" + "".join(f" * Step {index} explains itself.\n" for index in range(23)) + " */\n"
        self.assertEqual(self.heavy(block + script(0, 20))[0]["comment_lines"], 25)

    def test_test_generated_and_unknown_language_files_are_skipped(self):
        self.assertEqual(self.heavy(script(25, 20), "src/prices.test.js"), [])
        self.assertEqual(self.heavy("// Code generated by protoc. DO NOT EDIT.\n" + script(25, 20)), [])
        self.assertEqual(self.heavy(script(25, 20), "src/Prices.vue", "vue"), [])


class PlanMovesTest(unittest.TestCase):
    MISPLACED = {"path": "src/services/auth.js", "line": 4, "symbol": "authMiddleware", "role": "middleware",
                 "home_role": "service", "suggestion": "src/middleware/"}
    FAMILY = {"folder": "src", "token": "billing", "files": sorted(BILLING), "suggestion": "src/billing/"}

    def test_a_misplaced_symbol_and_a_family_are_two_moves_citing_their_finding(self):
        moves = structure_organization.plan_moves({"misplaced": [self.MISPLACED], "family": [self.FAMILY]})
        self.assertEqual(moves, [
            {"from": ["src/services/auth.js::authMiddleware"], "to": "src/middleware/", "why": "misplaced"},
            {"from": sorted(BILLING), "to": "src/billing/", "why": "family"},
        ])

    def test_a_file_holding_only_misplaced_code_moves_whole(self):
        misplaced = dict(self.MISPLACED, symbol=None, line=1, home_role=None)
        self.assertEqual(structure_organization.plan_moves({"misplaced": [misplaced]}),
                         [{"from": ["src/services/auth.js"], "to": "src/middleware/", "why": "misplaced"}])

    def test_a_finding_without_a_destination_is_no_move(self):
        self.assertEqual(structure_organization.plan_moves({"misplaced": [dict(self.MISPLACED, suggestion=None)]}),
                         [])
        described = dict(self.MISPLACED, suggestion="a file matching **/Data/**")
        self.assertEqual(structure_organization.plan_moves({"misplaced": [described]}), [])

    def test_symbols_moving_from_one_file_to_one_home_are_one_move(self):
        hooks = [dict(self.MISPLACED, path="src/api/hooks.ts", symbol=name, line=line, suggestion="src/hooks/")
                 for line, name in ((3, "useMe"), (9, "useUsers"))]
        other = dict(self.MISPLACED, path="src/api/hooks.ts", symbol="AuthGuard", line=20,
                     suggestion="src/guards/")
        self.assertEqual(structure_organization.plan_moves({"misplaced": hooks + [other]}), [
            {"from": ["src/api/hooks.ts::useMe", "src/api/hooks.ts::useUsers"], "to": "src/hooks/",
             "why": "misplaced"},
            {"from": ["src/api/hooks.ts::AuthGuard"], "to": "src/guards/", "why": "misplaced"},
        ])

    def test_a_junk_drawer_moves_each_split_that_has_a_destination(self):
        drawer = {"folder": "src/utils", "splits": [
            {"by": "role", "name": "repository", "files": ["src/utils/storage.py"], "to": None},
            {"by": "role", "name": "service", "files": ["src/utils/billing.py"], "to": "src/services/"},
            {"by": "unsorted", "name": None, "files": ["src/utils/pad.py"], "to": None},
        ], "rename": None}
        self.assertEqual(structure_organization.plan_moves({"junk_drawer": [drawer]}),
                         [{"from": ["src/utils/billing.py"], "to": "src/services/", "why": "junk_drawer"}])

    def test_a_junk_drawer_of_one_concept_moves_as_a_folder(self):
        drawer = {"folder": "src/utils", "rename": "src/date/", "splits": [
            {"by": "name", "name": "date", "files": ["src/utils/date_format.py", "src/utils/date_parse.py"],
             "to": None}]}
        self.assertEqual(structure_organization.plan_moves({"junk_drawer": [drawer]}),
                         [{"from": ["src/utils/"], "to": "src/date/", "why": "junk_drawer"}])

    def test_a_file_moves_once(self):
        family = dict(self.FAMILY, folder="src/utils", suggestion="src/utils/billing/",
                      files=[path.replace("src/", "src/utils/") for path in BILLING])
        drawer = {"folder": "src/utils", "splits": [
            {"by": "family", "name": "billing", "files": family["files"], "to": "src/billing/"},
            {"by": "role", "name": "service", "files": ["src/utils/orders.py"], "to": "src/services/"},
        ], "rename": None}
        moves = structure_organization.plan_moves({"family": [family], "junk_drawer": [drawer]})
        self.assertEqual([(move["to"], move["why"]) for move in moves],
                         [("src/billing/", "junk_drawer"), ("src/services/", "junk_drawer")])


FIXTURE = {
    ".clean/roles.md": "```clean-roles\nrole middleware = **/middleware/**\nrole service = **/services/**\n"
                       "signal middleware = \\(\\s*req\\b[^)]*,\\s*res\\b[^)]*,\\s*next\\b\n"
                       "name service = Service$\nname repository = Repository$\n```\n",
    "src/main.py": "from billing_invoice import invoice\nfrom utils import storage\n",
    "src/billing_invoice.py": "from billing_tax import tax\n\n\ndef invoice():\n    return tax()\n",
    "src/billing_tax.py": "from billing_export import export\n\n\ndef tax():\n    return export()\n",
    "src/billing_export.py": "def export():\n    return 1\n",
    "src/orphan.py": "def forgotten():\n    return 1\n",
    "src/tool.py": "def run():\n    pass\n\n\nif __name__ == '__main__':\n    run()\n",
    "src/utils/billing.py": "class BillingService:\n    pass\n",
    "src/utils/storage.py": "class InvoiceRepository:\n    pass\n",
    "web/notes.js": script(25, 20),
    "web/middleware/cors.js": "module.exports = function cors(req, res, next) { next(); };\n",
    "web/services/auth.js": "class AuthService {}\nfunction authMiddleware(req, res, next) { next(); }\n"
                            "module.exports = { AuthService, authMiddleware };\n",
    "web/app.js": "require('./notes');\nrequire('./services/auth');\nrequire('./middleware/cors');\n",
}


class OrganizationMapTest(unittest.TestCase):
    def test_the_map_reports_each_organization_finding(self):
        findings = map_of(FIXTURE)["findings"]
        self.assertEqual([(item["folder"], item["token"]) for item in findings["family"]], [("src", "billing")])
        self.assertEqual([item["folder"] for item in findings["junk_drawer"]], ["src/utils"])
        self.assertEqual(findings["flat_folder"], [])
        self.assertEqual([item["path"] for item in findings["unreferenced"]], ["src/orphan.py"])
        self.assertEqual([item["path"] for item in findings["comment_heavy"]], ["web/notes.js"])

    def test_the_map_plans_the_moves_its_findings_propose(self):
        moves = map_of(FIXTURE)["moves"]
        self.assertIn({"from": ["web/services/auth.js::authMiddleware"], "to": "web/middleware/",
                       "why": "misplaced"}, moves)
        self.assertIn({"from": ["src/billing_export.py", "src/billing_invoice.py", "src/billing_tax.py"],
                       "to": "src/billing/", "why": "family"}, moves)

    def test_an_accept_line_records_a_deliberate_exception(self):
        accepted = "accept src/orphan.py\naccept src/utils/**\naccept web/notes.js\n```\n"
        files = dict(FIXTURE, **{".clean/roles.md": FIXTURE[".clean/roles.md"][:-len("```\n")] + accepted})
        findings = map_of(files)["findings"]
        self.assertEqual((findings["unreferenced"], findings["junk_drawer"], findings["comment_heavy"]),
                         ([], [], []))

    def test_a_python_package_import_references_the_module_it_names(self):
        findings = map_of({"app.py": "from billing import tax\n", "billing/__init__.py": "",
                           "billing/tax.py": "def rate():\n    return 1\n"})["findings"]
        self.assertEqual(findings["unreferenced"], [])

    def test_a_package_that_imports_its_own_modules_references_them(self):
        data = map_of({"app.py": "from tools import devops\n", "tools/__init__.py": "from . import devops\n",
                       "tools/devops/__init__.py": "from . import (\n    boards,\n    wiki,\n)\n",
                       "tools/devops/boards.py": "TOOLS = ()\n", "tools/devops/wiki.py": "TOOLS = ()\n"})
        self.assertEqual(data["findings"]["unreferenced"], [])
        imports = {entry["path"]: entry["imports"] for entry in data["files"]}
        self.assertEqual(imports["tools/devops/__init__.py"], ["tools/devops/boards.py", "tools/devops/wiki.py"])
        self.assertEqual(imports["app.py"], ["tools/devops/__init__.py"])

    def test_this_repositorys_scripts_depend_on_the_modules_they_import(self):
        data = map_structure.build_map(support.REPO_ROOT, packs=[], depth=2)
        imports = {entry["path"]: entry["imports"] for entry in data["files"]}
        scripts = "skills/clean-code/scripts/"
        self.assertTrue({scripts + "source/files.py", scripts + "structure/findings.py"}
                        <= set(imports[scripts + "map_structure.py"]))

    def test_from_package_import_module_shows_the_family_and_the_dead_module(self):
        findings = map_of({
            "main.py": "from shop import billing_invoice\n", "shop/__init__.py": "",
            "shop/billing_invoice.py": "from shop import billing_tax\n",
            "shop/billing_tax.py": "from shop import billing_export\n",
            "shop/billing_export.py": "RATE = 1\n", "shop/dead.py": "UNUSED = 1\n",
        })["findings"]
        self.assertEqual([(item["folder"], item["token"]) for item in findings["family"]], [("shop", "billing")])
        self.assertEqual([item["path"] for item in findings["unreferenced"]], ["shop/dead.py"])

    def test_a_namespace_package_leaves_only_its_dead_module_unreferenced(self):
        findings = map_of({"main.py": "from shop import billing\nfrom shop.orders import cart\n",
                           "shop/billing.py": "RATE = 1\n", "shop/orders/cart.py": "ITEMS = []\n",
                           "shop/dead.py": "UNUSED = 1\n"})["findings"]
        self.assertEqual([item["path"] for item in findings["unreferenced"]], ["shop/dead.py"])

    def test_dead_modules_in_a_scripts_tree_are_reported(self):
        findings = map_of({
            "scripts/cli.py": "from source import files as project_files\nfrom structure import report\n\n\n"
                              "if __name__ == '__main__':\n    project_files.walk()\n",
            "scripts/source/__init__.py": "", "scripts/source/files.py": "def walk():\n    pass\n",
            "scripts/source/orphan.py": "def forgotten():\n    pass\n",
            "scripts/structure/__init__.py": "", "scripts/structure/report.py": "from . import findings\n",
            "scripts/structure/findings.py": "def find():\n    pass\n",
            "scripts/structure/stale.py": "def stale():\n    pass\n",
        })["findings"]
        self.assertEqual([item["path"] for item in findings["unreferenced"]],
                         ["scripts/source/orphan.py", "scripts/structure/stale.py"])

    def test_a_python_import_hides_no_file_of_another_language(self):
        findings = map_of({"app.py": "import logging\n", "web/main.ts": "export const main = 1;\n",
                           "web/logging/format.ts": "export const format = 1;\n"})["findings"]
        self.assertEqual([item["path"] for item in findings["unreferenced"]], ["web/logging/format.ts"])

    def test_the_packs_name_files_their_frameworks_load(self):
        data = map_of({
            "package.json": '{"dependencies": {"next": "15.5.0", "react": "19.0.0"}}\n',
            "app/page.tsx": "export default function Home() { return null; }\n",
            "app/robots.ts": "export default function robots() { return {}; }\n",
            "app/sitemap.ts": "export default function sitemap() { return []; }\n",
            "instrumentation.ts": "export function register() {}\n",
            "lib/unused.ts": "export const unused = 1;\n",
        }, ["references/frameworks/nextjs.md", "references/frameworks/react.md"])
        self.assertEqual([item["path"] for item in data["findings"]["unreferenced"]], ["lib/unused.ts"])
        data = map_of({
            "requirements.txt": "Django==5.2\n", "shop/__init__.py": "",
            "shop/apps.py": "from django.apps import AppConfig\n\n\nclass ShopConfig(AppConfig):\n    name = 'shop'\n",
            "shop/templatetags/__init__.py": "", "shop/templatetags/money.py": "def cents(value):\n    return value\n",
            "shop/signals.py": "def on_save():\n    pass\n", "shop/tasks.py": "def nightly():\n    pass\n",
            "shop/unused.py": "UNUSED = 1\n",
        }, ["references/frameworks/django.md"])
        self.assertEqual([item["path"] for item in data["findings"]["unreferenced"]], ["shop/unused.py"])


class ChangedTest(unittest.TestCase):
    """`--changed` limits findings to what git reports as changed or untracked."""

    FILES = {"src/orders.py": "def load_orders():\n    data = []\n    return data\n",
             "src/invoices.py": "def load_invoices():\n    tmp = []\n    return tmp\n"}

    def setUp(self):
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "project"
        write_files(self.root, self.FILES)

    def tearDown(self):
        self.directory.cleanup()

    def git(self, *arguments):
        # Isolated from the user's configuration: no hooks, signing, or identity of theirs.
        config = Path(self.directory.name) / "gitconfig"
        config.write_text("[user]\n\tname = Test\n\temail = test@example.com\n", encoding="utf-8")
        environment = dict(os.environ, GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM="1")
        subprocess.run(["git", *arguments], cwd=str(self.root), env=environment, check=True,
                       capture_output=True, text=True)

    def names_by_path(self, *argv):
        code, output, errors = run_map("--root", str(self.root), "--json", *argv)
        self.assertEqual(code, 0, errors)
        return sorted({item["path"] for item in json.loads(output)["findings"]["names"]}), errors

    def test_only_the_findings_of_changed_and_untracked_files_remain(self):
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "initial")
        with (self.root / "src" / "orders.py").open("a", encoding="utf-8") as handle:
            handle.write("\n\ndef count_orders():\n    tmp = 0\n    return tmp\n")
        write_files(self.root, {"src/refunds.py": "def load_refunds():\n    val = []\n    return val\n"})
        self.assertEqual(self.names_by_path()[0], ["src/invoices.py", "src/orders.py", "src/refunds.py"])
        paths, errors = self.names_by_path("--changed")
        self.assertEqual(paths, ["src/orders.py", "src/refunds.py"])
        self.assertEqual(errors, "")

    def test_outside_a_repository_it_maps_everything_with_a_note(self):
        with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": self.directory.name}):
            paths, errors = self.names_by_path("--changed")
        self.assertEqual(paths, ["src/invoices.py", "src/orders.py"])
        self.assertEqual(len(errors.strip().splitlines()), 1)
        self.assertIn("mapping every file", errors)

    def test_without_git_it_maps_everything_with_a_note(self):
        with mock.patch.object(map_structure.subprocess, "run", side_effect=FileNotFoundError("git")):
            paths, errors = self.names_by_path("--changed")
        self.assertEqual(paths, ["src/invoices.py", "src/orders.py"])
        self.assertIn("mapping every file", errors)

    def test_a_changed_view_never_replaces_the_saved_map(self):
        code, _, errors = run_map("--root", str(self.root), "--changed", "--write")
        self.assertEqual(code, 2)
        self.assertIn("--changed", errors)
        self.assertFalse((self.root / ".clean").exists())

    def test_a_folder_finding_stays_while_a_changed_file_sits_in_its_folder(self):
        write_files(self.root, {"src/billing_invoice.py": "from billing_tax import tax\n",
                                "src/billing_tax.py": "from billing_export import export\n",
                                "src/billing_export.py": "def export():\n    return 1\n",
                                "docs/notes.py": "NOTES = []\n"})
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "initial")

        def families():
            code, output, errors = run_map("--root", str(self.root), "--json", "--changed")
            self.assertEqual(code, 0, errors)
            return [item["folder"] for item in json.loads(output)["findings"]["family"]]

        (self.root / "docs" / "notes.py").write_text("NOTES = [1]\n", encoding="utf-8")
        self.assertEqual(families(), [])
        write_files(self.root, {"src/refunds.py": "REFUNDS = []\n"})
        self.assertEqual(families(), ["src"])


class OrganizationReportTest(unittest.TestCase):
    def setUp(self):
        self.data = map_of(FIXTURE)

    def test_proposed_moves_follow_the_findings_as_from_to_why(self):
        markdown = structure_report.render_markdown(self.data)
        positions = [markdown.index(heading) for heading in ("## Findings", "## Proposed moves", "## Tree")]
        self.assertEqual(positions, sorted(positions))
        moves = markdown.split("## Proposed moves", 1)[1].split("\n## ", 1)[0]
        self.assertIn("- `web/services/auth.js::authMiddleware` -> `web/middleware/` (misplaced)", moves)
        self.assertIn("- `src/billing_export.py, src/billing_invoice.py, src/billing_tax.py` -> `src/billing/` "
                      "(family)", moves)

    def test_proposed_moves_are_capped_with_a_pointer_to_structure_json(self):
        data = dict(self.data, moves=[{"from": [f"src/a{index}.py"], "to": "src/b/", "why": "family"}
                                      for index in range(4)])
        moves = structure_report.render_markdown(data, top=3).split("## Proposed moves", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(moves.count(" -> "), 3)
        self.assertIn("- ... and 1 more in structure.json", moves)

    def test_no_moves_say_so(self):
        markdown = structure_report.render_markdown(dict(self.data, moves=[]))
        self.assertIn("## Proposed moves\n\nNo moves proposed.", markdown)

    def test_each_organization_finding_is_listed_under_findings(self):
        findings = structure_report.render_markdown(self.data).split("## Findings", 1)[1].split("## Proposed")[0]
        for title in ("Families", "Junk drawers", "Flat folders", "Unreferenced", "Comment-heavy"):
            self.assertIn(f"| {title} |", findings)
        self.assertIn("`src/orphan.py` is possibly unused", findings)
        self.assertIn("`web/notes.js`: 25 of 45 lines are comments (56%)", findings)
        self.assertIn("group them in `src/billing/`", findings)

    def test_the_summary_counts_organization_findings_after_names(self):
        summary = structure_report.render_summary(self.data)
        self.assertRegex(summary, r"names \d+, families 1, junk drawers 1, flat folders 0, unreferenced 1, "
                                  r"comment-heavy 1\n")

    def test_a_junk_drawer_line_says_what_each_group_needs(self):
        split = {"folder": "src/utils", "rename": None, "splits": [
            {"by": "role", "name": "service", "files": ["src/utils/billing.py"], "to": "src/services/"},
            {"by": "name", "name": "date", "files": ["src/utils/date_format.py", "src/utils/date_parse.py"],
             "to": None},
            {"by": "unsorted", "name": None, "files": ["src/utils/slugify.py"], "to": None}]}
        renamed = {"folder": "src/helpers", "rename": "src/date/", "splits": [
            {"by": "name", "name": "date", "files": ["src/helpers/date_format.py", "src/helpers/date_parse.py"],
             "to": None}]}
        data = dict(self.data, findings=dict(self.data["findings"], junk_drawer=[split, renamed]))
        block = structure_report.render_markdown(data).split("### Junk drawers", 1)[1].split("\n### ", 1)[0]
        self.assertIn("service (`billing.py`) -> `src/services/`", block)
        self.assertIn("`date` (`date_format.py`, `date_parse.py`) share a name", block)
        self.assertIn("`slugify.py`: name the concept its files share", block)
        self.assertIn("`src/helpers/` holds one concept; rename it `src/date/`.", block)


class DocumentedDecisionsTest(unittest.TestCase):
    """What the organization findings do is written where agents and pack authors read it."""

    def read(self, relative):
        return (support.REPO_ROOT / relative).read_text(encoding="utf-8")

    def test_the_comment_workflow_says_api_doc_comments_are_not_counted(self):
        comments = self.read("skills/clean-code/references/comments.md")
        self.assertTrue(any("comment_heavy" in line and "doc comment" in line for line in comments.split("\n")))

    def test_the_references_and_docstrings_name_the_organization_findings(self):
        phase_b = self.read("skills/clean-code/references/audit-report.md").split("## Phase B", 1)[1]
        phase_b = phase_b.split("\n## ", 1)[0]
        for kind in ("families", "junk drawers", "flat folders", "unreferenced", "comment-heavy", "Proposed moves"):
            self.assertIn(kind, phase_b)
        self.assertIn("organization", structure_package.__doc__)
        roles_doc = structure_roles.__doc__
        self.assertIn("entry <glob>", roles_doc)
        self.assertIn("organization", roles_doc)
        grammar = self.read("skills/clean-code/references/framework-map.md").split("## Roles", 1)[1]
        self.assertIn("entry <glob>[, <glob>...]", grammar.split("```text", 1)[1].split("```", 1)[0])


if __name__ == "__main__":
    unittest.main()
