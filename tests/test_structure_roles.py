import tempfile
import textwrap
import unittest
from pathlib import Path

import support  # noqa: F401  (puts the scripts folder on sys.path)
import project_symbols
import structure_roles


def block(*lines):
    return "Prose around the block.\n\n```clean-roles\n" + "\n".join(lines) + "\n```\n"


def roles_from(*sources):
    statements = []
    for index, lines in enumerate(sources):
        statements += structure_roles.parse_roles(block(*lines), f"source{index}.md")
    return structure_roles.Roles(statements)


class ParseTest(unittest.TestCase):
    def test_every_statement_kind_parses(self):
        statements = structure_roles.parse_roles(block(
            "# comments and blank lines are ignored",
            "",
            "role middleware = **/middleware/**, **/*.middleware.*",
            "name hook = ^use[A-Z]",
            r"signal controller = @Controller\(",
            r"name component [tsx, .jsx] = ^[A-Z]\w*$",
            "ignore-name = ^(GET|POST)$",
        ), "pack.md")
        kinds = [(statement.kind, statement.role) for statement in statements]
        self.assertEqual(kinds, [("role", "middleware"), ("name", "hook"), ("signal", "controller"),
                                 ("name", "component"), ("ignore-name", None)])
        self.assertEqual(statements[0].value, ("**/middleware/**", "**/*.middleware.*"))
        self.assertEqual(statements[3].suffixes, ("tsx", "jsx"))
        self.assertEqual(statements[0].source, "pack.md:6")

    def test_text_without_a_block_declares_nothing(self):
        self.assertEqual(structure_roles.parse_roles("no block here", "x.md"), [])

    def test_allow_and_accept_parse(self):
        statements = structure_roles.parse_roles(block(
            "allow context = component, hook",
            "accept src/services/auth.js = handleAuthError, legacyGuard",
            "accept legacy/**",
        ), "roles.md")
        self.assertEqual([(statement.kind, statement.role, statement.value) for statement in statements], [
            ("allow", "context", ("component", "hook")),
            ("accept", None, ("src/services/auth.js", ("handleAuthError", "legacyGuard"))),
            ("accept", None, ("legacy/**", ())),
        ])

    def test_errors_name_the_file_and_line(self):
        cases = [
            ("unknown thing = x", "cannot parse"),
            ("role Middleware = **/x/**", "lowercase"),
            ("name hook = (", "invalid regex"),
            ("role middleware [ts] = **/x/**", "extension list"),
            ("allow Context = component", "lowercase"),
            ("allow context = component, Hook", "lowercase"),
            ("allow context", "cannot parse"),
            ("accept", "cannot parse"),
            ("accept src/auth.js =", "cannot parse"),
        ]
        for line, message in cases:
            with self.subTest(line=line):
                with self.assertRaises(structure_roles.RolesError) as raised:
                    structure_roles.parse_roles(block(line), "pack.md")
                self.assertIn("pack.md:4", str(raised.exception))
                self.assertIn(message, str(raised.exception))


class PrecedenceTest(unittest.TestCase):
    def test_earlier_sources_win(self):
        roles = roles_from(["signal service = @Injectable"], ["signal guard = @Injectable"])
        self.assertEqual(roles.intrinsic_role("Thing", "@Injectable()\nclass Thing", "ts"), "service")

    def test_signals_beat_names(self):
        roles = roles_from([r"signal guard = implements\s+CanActivate"], ["name service = Service$"])
        context = "@Injectable()\nexport class AuthService implements CanActivate {"
        self.assertEqual(roles.intrinsic_role("AuthService", context, "ts"), "guard")

    def test_extension_lists_limit_a_statement(self):
        roles = roles_from([r"name component [tsx] = ^[A-Z]\w*$"])
        self.assertEqual(roles.intrinsic_role("Button", "", "tsx"), "component")
        self.assertIsNone(roles.intrinsic_role("Button", "", "go"))

    def test_the_most_specific_home_glob_wins(self):
        roles = roles_from(["role service = **/services/**", "role middleware = **/*.middleware.*"])
        self.assertEqual(roles.home_role("src/services/auth.middleware.ts"), "middleware")
        self.assertEqual(roles.home_role("src/services/auth.ts"), "service")
        self.assertIsNone(roles.home_role("src/auth.ts"))

    def test_equal_specificity_goes_to_the_earlier_source(self):
        roles = roles_from(["role handler = **/api/**"], ["role route = **/api/**"])
        self.assertEqual(roles.home_role("src/api/users.ts"), "handler")

    def test_a_home_says_whether_only_a_file_name_grants_it(self):
        roles = roles_from(["role component = src/app/**/page.*, **/components/**",
                            "role service = **/services/**, **/*.service.*, **/*Service.*"])
        self.assertEqual(roles.home("src/app/orders/page.tsx"), ("component", True, "src/app/**/page.*"))
        self.assertEqual(roles.home("src/components/Card.tsx"), ("component", False, "**/components/**"))
        self.assertEqual(roles.home("src/billing/BillingService.java"), ("service", True, "**/*Service.*"))
        # The file name outweighs the folder here, but the folder is still a service home.
        self.assertEqual(roles.home("src/app/services/user.service.ts"),
                         ("service", False, "**/*.service.*"))
        self.assertEqual(roles.home("src/auth.ts"), (None, False, None))

    def test_allow_statements_from_every_source_apply(self):
        roles = roles_from(["allow context = component"], ["allow context = hook"])
        self.assertTrue(roles.allows("context", "component", "src/contexts/Auth.tsx"))
        self.assertTrue(roles.allows("context", "hook", "src/contexts/Auth.tsx"))
        self.assertFalse(roles.allows("context", "service", "src/contexts/Auth.tsx"))
        self.assertFalse(roles.allows("component", "context", "src/components/Card.tsx"))

    def test_a_scoped_allow_speaks_only_for_its_folders(self):
        statements = structure_roles.parse_roles(block("allow context = hook"), "react.md")
        roles = structure_roles.Roles([statement._replace(scope=("web",)) for statement in statements])
        self.assertTrue(roles.allows("context", "hook", "web/src/contexts/Auth.tsx"))
        self.assertFalse(roles.allows("context", "hook", "admin/src/contexts/Auth.tsx"))

    def test_accept_covers_a_whole_file_or_only_the_listed_symbols(self):
        roles = roles_from(["accept src/services/auth.js = handleAuthError", "accept legacy/**"])
        self.assertTrue(roles.accepts("src/services/auth.js", "handleAuthError"))
        self.assertFalse(roles.accepts("src/services/auth.js", "AuthService"))
        self.assertTrue(roles.accepts("legacy/old/billing.js", "anything"))
        self.assertFalse(roles.accepts("web/legacy/billing.js", "anything"))

    def test_ignored_names_and_home_globs(self):
        roles = roles_from(["role middleware = **/middleware/**", "ignore-name = ^(main|index)$"])
        self.assertTrue(roles.is_ignored_name("main"))
        self.assertFalse(roles.is_ignored_name("mainly"))
        self.assertEqual(roles.home_globs("middleware"), ["**/middleware/**"])


class LoadAndAssignTest(unittest.TestCase):
    def test_project_roles_come_before_packs_and_the_generic_block(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            project = Path(directory) / "project"
            (skill / "references" / "frameworks").mkdir(parents=True)
            (project / ".clean").mkdir(parents=True)
            (skill / "references" / "framework-map.md").write_text(
                block("name service = Service$"), encoding="utf-8")
            (skill / "references" / "frameworks" / "nest.md").write_text(
                block("name guard = Service$"), encoding="utf-8")
            (project / ".clean" / "roles.md").write_text(
                block("name action = Service$"), encoding="utf-8")
            roles = structure_roles.load_roles(skill, ["references/frameworks/nest.md"], project)
            self.assertEqual(roles.intrinsic_role("AuthService", "", "ts"), "action")
            (project / ".clean" / "roles.md").unlink()
            roles = structure_roles.load_roles(skill, ["frameworks/nest.md"], project)
            self.assertEqual(roles.intrinsic_role("AuthService", "", "ts"), "guard")

    def test_a_scoped_pack_speaks_only_for_files_under_its_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            (skill / "references" / "frameworks").mkdir(parents=True)
            (skill / "references" / "framework-map.md").write_text(
                block("role component = **/components/**"), encoding="utf-8")
            (skill / "references" / "frameworks" / "flutter.md").write_text(
                block("role widget = **/pages/**", "name widget = Page$"), encoding="utf-8")
            roles = structure_roles.load_roles(
                skill, ["references/frameworks/flutter.md"], Path(directory),
                {"references/frameworks/flutter.md": ["mobile"]})
        self.assertEqual(roles.home_role("mobile/lib/pages/login.dart"), "widget")
        self.assertIsNone(roles.home_role("web/src/pages/Profile.tsx"))
        self.assertEqual(roles.intrinsic_role("LoginPage", "", "dart", "mobile/lib/a.dart"), "widget")
        self.assertIsNone(roles.intrinsic_role("ProfilePage", "", "tsx", "web/src/a.tsx"))

    def test_a_scoped_pack_matches_its_globs_from_its_own_project_folder(self):
        statements = structure_roles.parse_roles(block("role entity = src/Entity/**"), "symfony.md")
        roles = structure_roles.Roles([statement._replace(scope=("services/billing",))
                                       for statement in statements])
        self.assertEqual(roles.home_role("services/billing/src/Entity/User.php"), "entity")
        self.assertIsNone(roles.home_role("src/Entity/User.php"))

    def test_assign_gives_top_level_symbols_a_role(self):
        roles = roles_from(["role service = **/services/**", "name middleware = Middleware$",
                            "name service = Service$"])
        source = textwrap.dedent("""
            export class AuthService {
              verify() {}
            }
            export function authMiddleware(req, res, next) {}
            """).lstrip("\n")
        roled = structure_roles.assign(
            project_symbols.extract("src/services/auth.ts", source), roles, is_test=False)
        self.assertEqual(roled.home_role, "service")
        by_name = {item.symbol.name: item.role for item in roled.symbols}
        self.assertEqual(by_name, {"AuthService": "service", "verify": None,
                                   "authMiddleware": "middleware"})


if __name__ == "__main__":
    unittest.main()
