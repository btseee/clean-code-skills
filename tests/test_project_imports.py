import tempfile
import textwrap
import unittest
from pathlib import Path

import support  # noqa: F401  (puts the scripts folder on sys.path)
import import_resolution
import project_imports
import project_symbols


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

    def test_jvm_package_and_type(self):
        index = build_index({
            "src/main/java/com/acme/order/OrderService.java":
                "package com.acme.order;\npublic class OrderService {}\n",
        })
        self.assertEqual(index.resolve("Other.java", "com.acme.order.OrderService"),
                         ["src/main/java/com/acme/order/OrderService.java"])
        self.assertEqual(index.resolve("Other.java", "com.acme.order.*"),
                         ["src/main/java/com/acme/order/OrderService.java"])

    def test_csharp_namespace(self):
        index = build_index({"Core/Orders/Order.cs": "namespace Acme.Core.Orders;\npublic class Order {}\n"})
        self.assertEqual(index.resolve("Web/Api.cs", "Acme.Core.Orders"), ["Core/Orders/Order.cs"])

    def test_php_namespace_and_class(self):
        index = build_index({
            "app/Services/Billing.php": "<?php\nnamespace App\\Services;\nclass Billing {}\n",
        })
        self.assertEqual(index.resolve("x.php", "App\\Services\\Billing"), ["app/Services/Billing.php"])

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
