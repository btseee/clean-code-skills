import unittest
from pathlib import Path

import support  # noqa: F401  (puts the scripts folder on sys.path)
import structure_findings as findings
import structure_roles
from structure_roles import RoledFile, RoledSymbol
from symbol_model import Symbol

GENERIC = structure_roles.Roles(structure_roles.parse_roles(
    "```clean-roles\n"
    "role middleware = **/middleware/**\n"
    "role service = **/services/**\n"
    "role guard = **/guards/**\n"
    "role model = **/models/**\n"
    "role route = **/routes/**\n"
    "ignore-name = ^(main|index)$\n"
    "```\n", "generic.md"))


def sym(name, kind="function", line=1, exported=True, parent=None, exact=None, shape=None,
        end_line=None):
    return Symbol(name, kind, line, end_line or line + 6, exported, parent, "", "", exact, shape)


def file(path, home, items, language="typescript", is_test=False):
    return RoledFile(path, language, Path(path).suffix.lstrip("."), home, is_test,
                     [RoledSymbol(symbol, role) for symbol, role in items], "", 20, 0, 0)


class MisplacedTest(unittest.TestCase):
    def test_a_foreign_role_in_a_home_folder_points_to_the_existing_home(self):
        files = [
            file("src/services/auth.ts", "service", [
                (sym("AuthService", "class", 1), "service"),
                (sym("authMiddleware", "function", 12), "middleware"),
            ]),
            file("src/middleware/cors.ts", "middleware", [(sym("corsMiddleware"), "middleware")]),
        ]
        result = findings.find_misplaced(files, GENERIC)
        self.assertEqual(result, [{
            "path": "src/services/auth.ts", "line": 12, "symbol": "authMiddleware",
            "role": "middleware", "home_role": "service", "suggestion": "src/middleware/",
        }])

    def test_without_an_existing_home_the_convention_names_the_folder(self):
        files = [file("src/services/auth.ts", "service", [
            (sym("AuthService", "class"), "service"),
            (sym("authMiddleware", line=12), "middleware"),
        ])]
        self.assertEqual(findings.find_misplaced(files, GENERIC)[0]["suggestion"], "src/middleware/")

    def test_a_homeless_file_with_one_role_moves_whole_when_a_home_exists(self):
        files = [
            file("src/guards.ts", None, [(sym("AdminGuard", "class"), "guard")]),
            file("src/guards/role.ts", "guard", [(sym("RoleGuard", "class"), "guard")]),
        ]
        self.assertEqual(findings.find_misplaced(files, GENERIC), [{
            "path": "src/guards.ts", "line": 1, "symbol": None, "role": "guard",
            "home_role": None, "suggestion": "src/guards/",
        }])

    def test_private_helpers_interfaces_and_tests_are_left_alone(self):
        files = [
            file("src/routes/users.ts", "route", [(sym("validate", exported=False), "middleware")]),
            file("src/models/user.ts", "model", [(sym("UserRepository", "interface"), "repository")]),
            file("src/services/auth.test.ts", "service", [(sym("fakeMiddleware"), "middleware")],
                 is_test=True),
        ]
        self.assertEqual(findings.find_misplaced(files, GENERIC), [])

    def test_languages_without_export_markers_count_every_top_level_symbol(self):
        files = [file("src/Services/Auth.cs", "service", [
            (sym("AuthMiddleware", "class", exported=False), "middleware"),
        ], language="csharp")]
        self.assertEqual(len(findings.find_misplaced(files, GENERIC)), 1)


class MixedTest(unittest.TestCase):
    def test_a_homeless_file_with_two_roles_is_mixed(self):
        files = [file("src/auth.ts", None, [
            (sym("AuthService", "class"), "service"),
            (sym("authMiddleware", line=12), "middleware"),
        ])]
        self.assertEqual(findings.find_mixed(files), [{
            "path": "src/auth.ts",
            "roles": {"middleware": ["authMiddleware"], "service": ["AuthService"]},
        }])
        self.assertEqual(findings.find_misplaced(files, GENERIC), [])


class DuplicateTest(unittest.TestCase):
    def test_identical_and_same_shape_groups(self):
        files = [
            file("src/a.ts", None, [(sym("total", exact="e1", shape="s1"), None),
                                    (sym("sum", exact="e2", shape="s2"), None)]),
            file("src/b.ts", None, [(sym("total", exact="e1", shape="s1"), None),
                                    (sym("add", exact="e3", shape="s2"), None)]),
            file("src/b.test.ts", None, [(sym("copy", exact="e1", shape="s1"), None)], is_test=True),
        ]
        result = findings.find_duplicates(files)
        kinds = sorted((group["kind"], len(group["members"])) for group in result)
        self.assertEqual(kinds, [("identical", 2), ("same shape", 2)])
        shape = next(group for group in result if group["kind"] == "same shape")
        self.assertEqual({member["symbol"] for member in shape["members"]}, {"sum", "add"})


class NameClashTest(unittest.TestCase):
    def test_one_type_name_in_two_files_of_a_language_family(self):
        files = [
            file("src/a.ts", None, [(sym("UserService", "class"), None)]),
            file("src/b.js", None, [(sym("UserService", "class"), None)], language="javascript"),
            file("cmd/a/main.go", None, [(sym("Config", "struct"), None)], language="go"),
            file("cmd/b/main.go", None, [(sym("Config", "struct"), None)], language="go"),
        ]
        result = findings.find_name_clashes(files, GENERIC)
        self.assertEqual([group["name"] for group in result], ["Config", "UserService"])
        self.assertEqual(len(result[1]["members"]), 2)

    def test_functions_clash_only_where_names_share_one_namespace(self):
        files = [
            file("src/a.ts", None, [(sym("formatDate"), None)]),
            file("src/b.ts", None, [(sym("formatDate"), None)]),
            file("src/list.c", None, [(sym("list_push"), None)], language="c"),
            file("src/queue.c", None, [(sym("list_push"), None)], language="c"),
            file("cmd/a/main.go", None, [(sym("main"), None)], language="go"),
        ]
        result = findings.find_name_clashes(files, GENERIC)
        self.assertEqual([group["name"] for group in result], ["list_push"])

    def test_private_names_never_clash(self):
        files = [
            file("src/Shape.java", None, [(sym("Helper", "class", exported=False), None)],
                 language="java"),
            file("src/Other.java", None, [(sym("Helper", "class", exported=False), None)],
                 language="java"),
        ]
        self.assertEqual(findings.find_name_clashes(files, GENERIC), [])


class SynonymTest(unittest.TestCase):
    def test_one_noun_with_several_retrieval_verbs(self):
        files = [
            file("src/a.ts", None, [(sym("getUser", line=1), None), (sym("fetchUser", line=9), None)]),
            file("src/b.ts", None, [(sym("getUserById", line=3), None),
                                    (sym("loadUsers", line=7), None),
                                    (sym("getAll", line=11), None),
                                    (sym("fetchAll", line=15), None)]),
            file("src/c.py", None, [(sym("remove_order"), None), (sym("delete_order"), None)],
                 language="python"),
        ]
        result = findings.find_synonyms(files, GENERIC)
        user = next(item for item in result if item["noun"] == "user")
        self.assertEqual(user["group"], "retrieve")
        self.assertEqual(sorted(user["verbs"]), ["fetch", "get", "load"])
        self.assertEqual(len(user["verbs"]["get"]), 2)
        self.assertTrue(any(item["noun"] == "order" and item["group"] == "delete" for item in result))
        self.assertFalse(any(item["noun"] == "all" for item in result))


class SplitIdentifierTest(unittest.TestCase):
    def test_camel_snake_kebab_and_acronyms(self):
        self.assertEqual(findings.split_identifier("getHTTPResponse"), ["get", "http", "response"])
        self.assertEqual(findings.split_identifier("load_users"), ["load", "users"])
        self.assertEqual(findings.split_identifier("Get-ChildItem"), ["get", "child", "item"])


if __name__ == "__main__":
    unittest.main()
