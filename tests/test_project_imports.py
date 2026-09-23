import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
import project_imports


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
