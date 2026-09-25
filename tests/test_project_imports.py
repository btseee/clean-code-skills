import tempfile
import textwrap
import unittest
from pathlib import Path

import support  # noqa: F401  (puts the scripts folder on sys.path)
import symbols as project_symbols
from source import imports as project_imports
from source import resolution as import_resolution


class ImportsInTextTest(unittest.TestCase):
    CASES = [
        (".ts", "import { a } from '../x';", [(1, "../x")]),
        (".mts", "import { a } from './y';", [(1, "./y")]),
        (".py", "from ..infra.db import Db", [(1, "..infra.db")]),
        (".go", 'import (\n  "fmt"\n  x "example.com/app/internal/auth"\n)',
         [(2, "fmt"), (3, "example.com/app/internal/auth")]),
        (".sh", 'source "$DIR/lib/log.sh"', [(1, "$DIR/lib/log.sh")]),
        (".sh", ". ./lib/env.sh", [(1, "./lib/env.sh")]),
        (".ps1", ". $PSScriptRoot\\Private\\Get-Thing.ps1",
         [(1, "$PSScriptRoot\\Private\\Get-Thing.ps1")]),
        (".psm1", "import-module ./Tools.psd1", [(1, "./Tools.psd1")]),
        (".ps1", "using module ..\\Shared\\Shared.psm1", [(1, "..\\Shared\\Shared.psm1")]),
        (".r", 'source("R/clean.R")\nlibrary(dplyr)', [(1, "R/clean.R"), (2, "dplyr")]),
        (".m", '#import "OrderService.h"', [(1, "OrderService.h")]),
        (".m", "@import UIKit;", [(1, "UIKit")]),
        (".h", "#import <Foundation/Foundation.h>", [(1, "Foundation/Foundation.h")]),
        (".cxx", '#include "geo/shape.h"', [(1, "geo/shape.h")]),
    ]

    def test_each_language_yields_its_imported_modules(self):
        for suffix, text, expected in self.CASES:
            with self.subTest(suffix=suffix, text=text):
                self.assertEqual(project_imports.imports_in_text(suffix, text), expected)

    def test_unknown_suffix_yields_nothing(self):
        self.assertEqual(project_imports.imports_in_text(".txt", "import x"), [])


def build_index(files):
    """A ModuleIndex over files (path -> text), built the way map_structure builds it."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for path, text in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
        index = import_resolution.ModuleIndex(root)
        for path, text in files.items():
            source = textwrap.dedent(text).lstrip("\n")
            index.add(path, source, project_symbols.extract(path, source))
    return index


class ModuleIndexTest(unittest.TestCase):
    def test_typescript_relative_import_of_a_folder_index(self):
        index = build_index({"src/a.ts": "", "src/lib/index.ts": ""})
        self.assertEqual(index.resolve("src/a.ts", "./lib"), ["src/lib/index.ts"])

    def test_tsconfig_path_aliases_tolerate_comments_and_trailing_commas(self):
        index = build_index({
            "tsconfig.json": """
                {
                  // editor settings live elsewhere
                  "compilerOptions": {
                    "baseUrl": ".",
                    "paths": { "@/*": ["src/*"], },
                  },
                }
                """,
            "src/a.ts": "",
            "src/util/date.ts": "",
        })
        self.assertEqual(index.resolve("src/a.ts", "@/util/date"), ["src/util/date.ts"])

    def test_python_dotted_modules_and_packages(self):
        index = build_index({
            "app/services/auth.py": "", "app/api/routes.py": "", "app/services/__init__.py": "",
        })
        self.assertEqual(index.resolve("app/api/routes.py", "app.services.auth"),
                         ["app/services/auth.py"])
        self.assertEqual(index.resolve("app/api/routes.py", "app.services"),
                         ["app/services/__init__.py"])

    def test_python_relative_import(self):
        index = build_index({"app/api/routes.py": "", "app/services/auth.py": ""})
        self.assertEqual(index.resolve("app/api/routes.py", "..services.auth"),
                         ["app/services/auth.py"])

    def test_python_from_import_resolves_the_module_it_names_else_the_package(self):
        index = build_index({"shop/__init__.py": "", "shop/tax.py": "", "shop/billing/__init__.py": "",
                             "shop/billing/invoice.py": "", "shop/billing/export.py": "", "app.py": ""})
        text = ("from shop import tax, rate as shop_rate\nfrom shop.billing import invoice\n"
                "from shop import *\nimport shop.tax, json\n")
        self.assertEqual([index.resolve("app.py", module)
                          for module in project_imports.resolvable_imports(".py", text)],
                         [["shop/tax.py"], ["shop/__init__.py"], ["shop/billing/invoice.py"],
                          ["shop/__init__.py"], ["shop/tax.py"], []])
        relative = project_imports.resolvable_imports(".py", "from . import export\nfrom .. import tax, total\n")
        self.assertEqual([index.resolve("shop/billing/invoice.py", module) for module in relative],
                         [["shop/billing/export.py"], ["shop/tax.py"], ["shop/__init__.py"]])

    def test_a_parenthesized_python_import_names_each_module(self):
        index = build_index({"tools/__init__.py": "", "tools/boards.py": "", "tools/wiki.py": ""})
        text = 'from . import (\n    boards,  # the boards tools\n    wiki,\n)\n"""from . import nothing"""\n'
        self.assertEqual([index.resolve("tools/__init__.py", module)
                          for module in project_imports.resolvable_imports(".py", text)],
                         [["tools/boards.py"], ["tools/wiki.py"]])

    def test_an_unresolved_from_import_is_recorded_by_its_module_never_the_name(self):
        modules = project_imports.resolvable_imports(".py", "from django.db import models\n")
        self.assertEqual([project_imports.imported_module(module) for module in modules], ["django.db"])
        self.assertEqual(project_imports.imported_module("lodash/debounce"), "lodash/debounce")

    def test_a_jvm_package_import_names_no_file_but_its_types_do(self):
        order = "src/main/java/com/acme/order/OrderService.java"
        index = build_index({
            order: "package com.acme.order;\npublic class OrderService {}\n",
            "src/main/java/com/acme/order/Unused.java": "package com.acme.order;\npublic class Unused {}\n",
            "src/main/java/com/acme/web/Api.java":
                "package com.acme.web;\nimport com.acme.order.*;\npublic class Api { OrderService s; }\n",
        })
        self.assertEqual(index.resolve("Other.java", "com.acme.order.OrderService"), [order])
        self.assertEqual(index.resolve("Other.java", "com.acme.order.*"), [])
        self.assertEqual(index.resolve_type_references("src/main/java/com/acme/web/Api.java"), [order])

    def test_a_kotlin_import_of_a_top_level_function_names_its_file(self):
        card = "app/src/main/kotlin/com/shop/ui/OrderCard.kt"
        index = build_index({
            card: "package com.shop.ui\n\n@Composable\nfun OrderCard(title: String) {\n    Text(title)\n}\n",
            "app/src/main/kotlin/com/shop/ui/Theme.kt": "package com.shop.ui\n\nfun ShopTheme() {}\n",
        })
        self.assertEqual(index.resolve("Screen.kt", "com.shop.ui.OrderCard"), [card])
        self.assertEqual(index.resolve("Screen.kt", "com.shop.ui.Missing"), [])

    def test_a_csharp_namespace_using_names_no_file_but_its_types_do(self):
        index = build_index({
            "Core/Orders/Order.cs": "namespace Acme.Core.Orders;\npublic class Order {}\n",
            "Core/Orders/Formats.cs": "namespace Acme.Core.Orders;\npublic static class Formats {}\n",
            "Core/Orders/Status.cs": "namespace Acme.Core.Orders;\npublic enum Status { Open }\n",
            "Web/Api.cs": "using Acme.Core.Orders;\nusing static Acme.Core.Orders.Formats;\n"
                          "namespace Acme.Web;\npublic class Api { Order o; }\n",
        })
        self.assertEqual(index.resolve("Web/Api.cs", "Acme.Core.Orders"), [])
        self.assertEqual(index.resolve("Web/Api.cs", "Acme.Core.Orders.Formats"), ["Core/Orders/Formats.cs"])
        self.assertEqual(index.resolve_type_references("Web/Api.cs"),
                         ["Core/Orders/Formats.cs", "Core/Orders/Order.cs"])

    def test_a_namespace_two_projects_declare_draws_no_edge_back(self):
        # A file's using of its own namespace, which a service project also declares,
        # made the contract depend on its implementation: a cycle no compiler allows.
        index = build_index({
            "Exchange/Validation/IResults.cs": "namespace App.Exchange.Validation\n{\n"
                                               "    using App.Exchange.Validation;\n"
                                               "    public interface IResults { string Name { get; } }\n}\n",
            "Services/Validation/Results.cs": "namespace App.Exchange.Validation\n{\n"
                                              "    public class Results : IResults { }\n}\n",
        })
        self.assertEqual(index.resolve("Exchange/Validation/IResults.cs", "App.Exchange.Validation"), [])
        self.assertEqual(index.resolve_type_references("Exchange/Validation/IResults.cs"), [])
        self.assertEqual(index.resolve_type_references("Services/Validation/Results.cs"),
                         ["Exchange/Validation/IResults.cs"])

    def test_csharp_reaches_attributes_and_extension_methods_without_their_full_type_names(self):
        index = build_index({
            "Security/UseSecurityAttribute.cs":
                "namespace App.Security;\npublic class UseSecurityAttribute : System.Attribute {}\n",
            "Core/Extension/DbExtension.cs":
                "namespace App.Core.Extension;\npublic static class DbExtension\n{\n"
                "    public static T MapData<T>(this DbDataReader reader) where T : class\n"
                "    {\n        return null;\n    }\n}\n",
            "Core/Extension/NumberExtension.cs":
                "namespace App.Core.Extension;\npublic static class NumberExtension\n{\n"
                "    public static int Twice(this int value) => value * 2;\n}\n",
            "Audit/Settings.cs":
                "using App.Security;\nusing App.Core.Extension;\nnamespace App.Audit;\n[UseSecurity]\n"
                "public class Settings\n{\n    public Settings Load(DbDataReader reader) => "
                "reader.MapData<Settings>();\n}\n",
        })
        self.assertEqual(index.resolve_type_references("Audit/Settings.cs"),
                         ["Core/Extension/DbExtension.cs", "Security/UseSecurityAttribute.cs"])

    def test_php_namespace_and_class(self):
        index = build_index({
            "app/Services/Billing.php": "<?php\nnamespace App\\Services;\nclass Billing {}\n",
        })
        self.assertEqual(index.resolve("x.php", "App\\Services\\Billing"), ["app/Services/Billing.php"])
        self.assertEqual(index.resolve("x.php", "App\\Services"), [])

    def test_go_module_paths_skip_test_files(self):
        index = build_index({
            "go.mod": "module example.com/app\n",
            "internal/auth/auth.go": "package auth\n",
            "internal/auth/auth_test.go": "package auth\n",
            "cmd/api/main.go": "package main\n",
        })
        self.assertEqual(index.resolve("cmd/api/main.go", "example.com/app/internal/auth"),
                         ["internal/auth/auth.go"])

    def test_rust_crate_paths(self):
        index = build_index({"src/lib.rs": "", "src/domain/order.rs": ""})
        self.assertEqual(index.resolve("src/lib.rs", "crate::domain::order::Order"),
                         ["src/domain/order.rs"])

    def test_dart_own_package(self):
        index = build_index({"pubspec.yaml": "name: shop\n", "lib/src/cart.dart": "", "lib/main.dart": ""})
        self.assertEqual(index.resolve("lib/main.dart", "package:shop/src/cart.dart"),
                         ["lib/src/cart.dart"])
        self.assertEqual(index.resolve("lib/main.dart", "package:flutter/material.dart"), [])

    def test_c_include_through_an_include_folder(self):
        index = build_index({"include/geo/shape.h": "", "src/shape.c": ""})
        self.assertEqual(index.resolve("src/shape.c", "geo/shape.h"), ["include/geo/shape.h"])

    def test_system_includes_resolve_only_by_their_path(self):
        index = build_index({"src/net/ssl.h": "", "src/core/time.h": "", "src/app/main.c": "",
                             "include/mylib/api.h": ""})
        modules = project_imports.resolvable_imports(
            ".c", '#include <openssl/ssl.h>\n#include <sys/time.h>\n#include <mylib/api.h>\n'
                  '#include "time.h"\n')
        self.assertEqual([index.resolve("src/app/main.c", module) for module in modules],
                         [[], [], ["include/mylib/api.h"], ["src/core/time.h"]])

    def test_typescript_esm_imports_name_the_emitted_file(self):
        index = build_index({"src/api/routes.ts": "", "src/domain/order.ts": "", "src/ui/view.tsx": "",
                             "src/ui/app.tsx": "", "src/lib/a.mts": "", "src/lib/b.cts": ""})
        cases = [
            ("src/api/routes.ts", "../domain/order.js", ["src/domain/order.ts"]),
            ("src/ui/app.tsx", "./view.jsx", ["src/ui/view.tsx"]),
            ("src/ui/app.tsx", "./view.js", ["src/ui/view.tsx"]),
            ("src/api/routes.ts", "../lib/a.mjs", ["src/lib/a.mts"]),
            ("src/api/routes.ts", "../lib/b.cjs", ["src/lib/b.cts"]),
        ]
        for source, module, expected in cases:
            with self.subTest(module=module):
                self.assertEqual(index.resolve(source, module), expected)

    def test_shell_source_with_a_script_directory_prefix(self):
        index = build_index({"scripts/lib/log.sh": "", "scripts/deploy.sh": ""})
        module = project_imports.imports_in_text(".sh", 'source "$(dirname "$0")/lib/log.sh"')[0][1]
        self.assertEqual(index.resolve("scripts/deploy.sh", module), ["scripts/lib/log.sh"])

    def test_external_packages_resolve_to_nothing(self):
        index = build_index({"src/a.ts": ""})
        self.assertEqual(index.resolve("src/a.ts", "react"), [])

    def test_type_references_resolve_unique_names_outside_comments(self):
        index = build_index({
            "Sources/App/Cart.swift": "struct Cart {}\n",
            "Sources/App/CheckoutView.swift":
                "struct CheckoutView: View {\n  let cart = Cart()\n  // Receipt in a comment\n}\n",
            "Sources/App/Receipt.swift": "struct Receipt {}\n",
        })
        self.assertEqual(index.resolve_type_references("Sources/App/CheckoutView.swift"),
                         ["Sources/App/Cart.swift"])

    def test_csharp_type_references_see_only_visible_namespaces(self):
        files = {
            "Other/Settings.cs": "namespace Other;\npublic class Settings {}\n",
            "App/Core/Clock.cs": "namespace App.Core;\npublic class Clock {}\n",
            "App/Core/Jobs/Runner.cs":
                "namespace App.Core.Jobs;\npublic class Runner { Settings s; Clock c; }\n",
        }
        index = build_index(files)
        self.assertEqual(index.resolve_type_references("App/Core/Jobs/Runner.cs"),
                         ["App/Core/Clock.cs"])
        files["App/Core/Jobs/Runner.cs"] = ("using Other;\nnamespace App.Core.Jobs;\n"
                                            "public class Runner { Settings s; Clock c; }\n")
        index = build_index(files)
        self.assertEqual(index.resolve_type_references("App/Core/Jobs/Runner.cs"),
                         ["App/Core/Clock.cs", "Other/Settings.cs"])

    def test_an_import_does_not_make_its_parent_namespace_visible(self):
        index = build_index({
            "src/Domain/Status.cs": "namespace Shop.Domain;\npublic enum Status { Ok }\n",
            "src/Domain/Orders/Order.cs": "namespace Shop.Domain.Orders;\npublic class Order {}\n",
            "src/Web/HealthController.cs":
                "using Shop.Domain.Orders;\nnamespace Shop.Web;\npublic class HealthController {\n"
                "  public int Status { get; set; }\n  public Order Last { get; set; }\n}\n",
            "java/com/acme/order/Priority.java": "package com.acme.order;\npublic enum Priority { HIGH }\n",
            "java/com/acme/order/OrderService.java":
                "package com.acme.order;\npublic class OrderService {}\n",
            "java/com/acme/web/Health.java":
                "package com.acme.web;\nimport com.acme.order.OrderService;\n"
                "public class Health { int Priority; OrderService service; }\n",
        })
        self.assertEqual(index.resolve_type_references("src/Web/HealthController.cs"),
                         ["src/Domain/Orders/Order.cs"])
        self.assertEqual(index.resolve_type_references("java/com/acme/web/Health.java"), [])
        self.assertEqual(index.resolve("java/com/acme/web/Health.java", "com.acme.order.OrderService"),
                         ["java/com/acme/order/OrderService.java"])

    def test_a_using_inside_a_namespace_block_is_relative_to_it(self):
        index = build_index({
            "Core/Application.cs": "namespace Inklusit.Core\n{\n    public static class Application {}\n}\n",
            "Core/Status.cs": "namespace Inklusit.Core\n{\n    public enum Status { Ok }\n}\n",
            "Services/Cluster.cs":
                "using Core;\nnamespace Inklusit.Service.Cluster\n{\n    using Core;\n\n"
                "    public class Cluster { void Run() { Application.Start(); } }\n}\n",
            "Services/Top.cs":
                "using Core;\nnamespace Inklusit.Service.Top;\npublic class Top { Status s; }\n",
        })
        self.assertEqual(index.resolve_type_references("Services/Cluster.cs"), ["Core/Application.cs"])
        self.assertEqual(index.resolve_type_references("Services/Top.cs"), [])

    def test_ambiguous_type_names_resolve_to_nothing(self):
        index = build_index({
            "A/User.cs": "namespace A;\npublic class User {}\n",
            "B/User.cs": "namespace B;\npublic class User {}\n",
            "C/Use.cs": "namespace C;\npublic class Use { User u; }\n",
        })
        self.assertEqual(index.resolve_type_references("C/Use.cs"), [])


class ResolveRelativeImportTest(unittest.TestCase):
    def test_moved_resolver_keeps_its_behavior(self):
        files = {"src/domain/order.py", "src/infra/db.py"}
        exists = files.__contains__
        self.assertEqual(
            project_imports.resolve_relative_import("src/domain/order.py", "..infra.db", exists),
            "src/infra/db.py",
        )
        self.assertIsNone(
            project_imports.resolve_relative_import("src/domain/order.ts", "../../../etc", exists)
        )
        self.assertIsNone(project_imports.resolve_relative_import("src/a.ts", "react", exists))


if __name__ == "__main__":
    unittest.main()
