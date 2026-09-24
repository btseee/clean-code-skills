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


def with_statements(*lines):
    """The generic conventions plus the given clean-roles statements, as a project adds them."""
    added = structure_roles.parse_roles("```clean-roles\n" + "\n".join(lines) + "\n```\n", "roles.md")
    return structure_roles.Roles(added + GENERIC.statements)


def sym(name, kind="function", line=1, exported=True, parent=None, exact=None, shape=None,
        end_line=None):
    return Symbol(name, kind, line, end_line or line + 6, exported, parent, "", "", exact, shape)


def file(path, home, items, language="typescript", is_test=False, by_name=False):
    return RoledFile(path, language, Path(path).suffix.lstrip("."), home, is_test,
                     [RoledSymbol(symbol, role) for symbol, role in items], "", 20, 0, 0,
                     home_by_name=by_name)


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

    def test_the_nearest_home_wins_over_a_busier_one_in_another_project(self):
        files = [
            file("web/src/services/auth.ts", "service", [
                (sym("AuthService", "class"), "service"),
                (sym("authMiddleware", line=12), "middleware"),
            ]),
            file("web/src/middleware/log.ts", "middleware", [(sym("logMiddleware"), "middleware")]),
        ] + [file(f"api/src/middleware/m{n}.ts", "middleware", [(sym(f"m{n}Middleware"), "middleware")])
             for n in range(3)]
        self.assertEqual(findings.find_misplaced(files, GENERIC)[0]["suggestion"],
                         "web/src/middleware/")

    def test_a_suggestion_never_leaves_the_files_own_project(self):
        files = [
            file("Core/Services/auth.ts", "service", [
                (sym("AuthService", "class"), "service"),
                (sym("authMiddleware", line=12), "middleware"),
            ]),
            file("Exchange/middleware/cors.ts", "middleware", [(sym("corsMiddleware"), "middleware")]),
        ]
        self.assertEqual(findings.find_misplaced(files, GENERIC)[0]["suggestion"],
                         "Exchange/middleware/")
        suggestion = findings.find_misplaced(files, GENERIC, ["", "Core", "Exchange"])[0]["suggestion"]
        self.assertEqual(suggestion, "Core/Middleware/")  # cased like its sibling Core/Services

    def test_a_new_folder_takes_the_casing_of_the_folders_beside_it(self):
        roles = with_statements("role config = **/configuration/**", "role validator = **/validators/**")
        pascal = [
            file("Core/Configuration/TypeValidator.cs", "config",
                 [(sym("TypeValidator", "class"), "validator")], language="csharp"),
            file("Core/Caching/Cache.cs", None, [(sym("Cache", "class"), None)], language="csharp"),
        ]
        self.assertEqual(findings.find_misplaced(pascal, roles, ["Core"])[0]["suggestion"],
                         "Core/Validators/")
        lower = [file("src/configuration/typeValidator.ts", "config",
                      [(sym("TypeValidator", "class"), "validator")])]
        self.assertEqual(findings.find_misplaced(lower, roles)[0]["suggestion"], "src/validators/")

    def test_a_new_csharp_folder_with_no_folders_beside_it_is_pascal_case(self):
        files = [file("Api/AuthService.cs", "service", [(sym("AuthMiddleware", "class"), "middleware")],
                      language="csharp")]
        self.assertEqual(findings.find_misplaced(files, GENERIC, ["Api"])[0]["suggestion"],
                         "Api/Middleware/")

    def test_no_folder_is_invented_at_the_repository_root(self):
        files = [file("AuthService.cs", "service", [(sym("AuthMiddleware", "class"), "middleware")],
                      language="csharp")]
        self.assertEqual(findings.find_misplaced(files, GENERIC)[0]["suggestion"],
                         "a file matching **/middleware/**")

    def test_a_home_named_for_the_role_beside_the_file_wins_over_a_distant_folder(self):
        roles = with_statements("role view = **/views.py", "role model = **/models.py, **/models/**")
        files = [
            file("shop/orders/views.py", "view", [(sym("Refund", "class"), "model")], language="python"),
            file("shop/orders/models.py", "model", [(sym("Order", "class"), "model")],
                 language="python", by_name=True),
            file("core/models/base.py", "model", [(sym("Base", "class"), "model")], language="python"),
        ]
        self.assertEqual(findings.find_misplaced(files, roles)[0]["suggestion"], "shop/orders/models.py")

    def test_a_file_already_named_for_the_role_is_sent_to_the_roles_folder(self):
        # TypeValidator.cs is named like a validator, and its folder makes it config: a file
        # "named like *Validator.*" beside it would be itself.
        roles = with_statements("role config = **/configuration/**",
                                "role validator = **/validators/**, **/*Validator.*")
        files = [
            file("Core/Configuration/TypeValidator.cs", "config",
                 [(sym("TypeValidator", "class"), "validator")], language="csharp"),
            file("Core/Rules/NameValidator.cs", "validator", [(sym("NameValidator", "class"), "validator")],
                 language="csharp", by_name=True),
        ]
        self.assertEqual(findings.find_misplaced(files, roles, ["Core"])[0]["suggestion"],
                         "Core/Validators/")

    def test_a_jvm_convention_folder_sits_under_the_base_package(self):
        shop = "src/main/java/com/acme/shop"
        files = [
            file(f"{shop}/order/OrderController.java", "controller",
                 [(sym("OrderCache", "class"), "repository")], language="java"),
            file(f"{shop}/billing/Invoice.java", None, [(sym("Invoice", "class"), None)], language="java"),
        ]
        roles = with_statements("role controller = **/*Controller.*", "role repository = **/repository/**")
        self.assertEqual(findings.find_misplaced(files, roles)[0]["suggestion"], f"{shop}/repository/")

    def test_an_entry_point_is_never_told_to_move_whole(self):
        files = [
            file("lib/main.dart", None, [(sym("LoginApp", "class"), "guard")], language="dart"),
            file("lib/guards/role.dart", "guard", [(sym("RoleGuard", "class"), "guard")],
                 language="dart"),
        ]
        self.assertEqual(findings.find_misplaced(files, GENERIC), [])

    def test_feature_folders_are_not_told_to_move_to_a_distant_home(self):
        files = [
            file("src/app/users/user.guard.ts", None, [(sym("UserGuard", "class"), "guard")]),
            file("src/app/core/guards/role.ts", "guard", [(sym("RoleGuard", "class"), "guard")]),
        ]
        self.assertEqual(findings.find_misplaced(files, GENERIC), [])

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

    def test_an_allowed_role_may_live_in_a_home_of_another(self):
        roles = with_statements("allow route = middleware")
        files = [
            file("src/routes/users.ts", "route", [(sym("requireAuth", line=3), "middleware")]),
            file("src/services/auth.ts", "service", [(sym("authMiddleware", line=5), "middleware")]),
        ]
        self.assertEqual([item["path"] for item in findings.find_misplaced(files, roles)],
                         ["src/services/auth.ts"])

    def test_an_accepted_symbol_or_file_is_not_misplaced(self):
        files = [
            file("src/services/auth.ts", "service", [
                (sym("handleAuthError", line=3), "middleware"),
                (sym("authMiddleware", line=9), "middleware"),
            ]),
            file("src/guards.ts", None, [(sym("AdminGuard", "class"), "guard")]),
            file("src/guards/role.ts", "guard", [(sym("RoleGuard", "class"), "guard")]),
        ]
        self.assertEqual([(item["path"], item["symbol"]) for item in findings.find_misplaced(files, GENERIC)],
                         [("src/guards.ts", None), ("src/services/auth.ts", "handleAuthError"),
                          ("src/services/auth.ts", "authMiddleware")])
        roles = with_statements("accept src/services/auth.ts = handleAuthError", "accept src/guards.ts")
        self.assertEqual([(item["path"], item["symbol"]) for item in findings.find_misplaced(files, roles)],
                         [("src/services/auth.ts", "authMiddleware")])


class MixedTest(unittest.TestCase):
    def test_a_homeless_file_with_two_roles_is_mixed(self):
        files = [file("src/auth.ts", None, [
            (sym("AuthService", "class"), "service"),
            (sym("authMiddleware", line=12), "middleware"),
        ])]
        self.assertEqual(findings.find_mixed(files, GENERIC), [{
            "path": "src/auth.ts",
            "roles": {"middleware": ["authMiddleware"], "service": ["AuthService"]},
        }])
        self.assertEqual(findings.find_misplaced(files, GENERIC), [])

    def test_an_accepted_file_or_symbol_is_not_mixed(self):
        files = [file("src/auth.ts", None, [
            (sym("AuthService", "class"), "service"),
            (sym("authMiddleware", line=12), "middleware"),
        ])]
        for statement in ("accept src/auth.ts", "accept **/auth.ts = authMiddleware"):
            with self.subTest(statement=statement):
                self.assertEqual(findings.find_mixed(files, with_statements(statement)), [])


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

    def test_components_named_after_route_files_never_clash(self):
        # The scanner names a .svelte or .vue component after its file; a framework's
        # route files share their names, and their identity is the path.
        components = [("src/routes/+page.svelte", "Page"), ("src/routes/about/+page.svelte", "Page"),
                      ("pages/orders/index.vue", "Index"), ("pages/users/index.vue", "Index"),
                      ("layouts/default.vue", "Default"), ("admin/layouts/default.vue", "Default"),
                      ("src/a/UserCard.vue", "UserCard"), ("src/b/UserCard.vue", "UserCard")]
        files = [file(path, None, [(sym(name, "component"), None)], language=path.rsplit(".", 1)[1])
                 for path, name in components]
        self.assertEqual([group["name"] for group in findings.find_name_clashes(files, GENERIC)],
                         ["UserCard"])

    def test_components_named_like_route_files_outside_route_folders_still_clash(self):
        components = [("src/components/shop/Error.vue", "Error"),
                      ("src/components/admin/Error.vue", "Error")]
        files = [file(path, None, [(sym(name, "component"), None)], language="vue")
                 for path, name in components]
        self.assertEqual([group["name"] for group in findings.find_name_clashes(files, GENERIC)],
                         ["Error"])

    def test_names_clash_only_within_one_project(self):
        files = [file(path, None, [(sym("Database", "class"), None)], language="csharp")
                 for path in ("Services/Audit/Database.cs", "Services/State/Database.cs",
                              "Services/State/Legacy/Database.cs")]
        result = findings.find_name_clashes(files, GENERIC, ["Services/Audit", "Services/State"])
        self.assertEqual([[member["path"] for member in group["members"]] for group in result],
                         [["Services/State/Database.cs", "Services/State/Legacy/Database.cs"]])

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
