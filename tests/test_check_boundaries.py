import json
import tempfile
import unittest
from pathlib import Path

import support  # puts the scripts folder on sys.path
import check_boundaries as cb


class ClassificationTest(unittest.TestCase):
    """The same table CI runs, so moving the import parser cannot change a verdict."""

    def test_imports_are_placed_the_same_way_for_paths_and_module_names(self):
        layering = cb.parse_layering(
            "```clean-architecture\nlayer domain = src/domain/**\n"
            "layer infra = src/infra/**\nallow domain -> *\n```"
        )
        files = {"src/domain/order.py", "src/domain/order.ts", "src/infra/db.py", "src/infra/db.ts"}
        exists = files.__contains__
        cases = [
            ("src/domain/order.py", "..infra.db", "infra"),
            ("src/domain/order.py", "..missing.thing", None),
            ("src/domain/order.py", "app.infra.db", "infra"),
            ("src/domain/order.py", "json", None),
            ("src/domain/order.ts", "../infra/db", "infra"),
            ("src/domain/order.ts", "./order", "domain"),
            ("src/domain/order.ts", "../../../etc", None),
            ("src/domain/order.ts", "react", None),
        ]
        for source, module, want in cases:
            with self.subTest(source=source, module=module):
                self.assertEqual(layering.layer_of_import(module, source, exists), want)
        self.assertTrue(layering.permits("infra", "domain"))
        self.assertTrue(layering.permits("domain", "infra"))
        plain = cb.parse_layering(
            "```clean-architecture\nlayer domain = src/domain/**\nlayer infra = src/infra/**\n```"
        )
        self.assertFalse(plain.permits("domain", "infra"))

    def test_a_leading_double_star_also_matches_a_top_level_folder(self):
        layering = cb.parse_layering(
            "```clean-architecture\nlayer domain = **/domain/**\nlayer ui = **/components/**\n```"
        )
        for path, want in [("domain/order.ts", "domain"), ("app/domain/order.ts", "domain"),
                           ("components/Cart.vue", "ui"), ("src/components/Cart.vue", "ui"),
                           ("mydomain/order.ts", None)]:
            with self.subTest(path=path):
                self.assertEqual(layering.layer_of_path(path), want)

    def test_source_root_folders_are_not_namespace_tokens(self):
        layering = cb.parse_layering(
            "```clean-architecture\nlayer domain = src/main/java/**/domain/**\n"
            "layer web = src/main/java/**/web/**\nlayer core = include/*/core/**, R/core-*.R\n```"
        )
        self.assertEqual(layering.namespaces["domain"], ["domain"])
        self.assertEqual(layering.namespaces["core"], ["core"])
        self.assertIsNone(layering.layer_of_name("java.util.List"))
        self.assertEqual(layering.layer_of_name("com.example.web.OrderController"), "web")


class CheckProjectTest(unittest.TestCase):
    def test_an_outward_import_is_a_violation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src" / "domain").mkdir(parents=True)
            (root / "src" / "infra").mkdir(parents=True)
            (root / "src" / "domain" / "order.ts").write_text(
                "import { Db } from '../infra/db';\n", encoding="utf-8"
            )
            (root / "src" / "infra" / "db.ts").write_text("export const Db = 1;\n", encoding="utf-8")
            layering = cb.parse_layering(
                "```clean-architecture\nlayer domain = src/domain/**\nlayer infra = src/infra/**\n```"
            )
            result = cb.check_project(root, layering)
        self.assertEqual(result["violation_count"], 1)
        self.assertEqual(result["violations"][0]["to_layer"], "infra")

    def test_a_file_name_the_console_cannot_encode_is_still_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".clean").mkdir()
            (root / ".clean" / "architecture.md").write_text(
                "```clean-architecture\nlayer domain = src/domain/**\nlayer infra = src/infra/**\n```\n",
                encoding="utf-8")
            (root / "src" / "domain").mkdir(parents=True)
            (root / "src" / "infra").mkdir(parents=True)
            (root / "src" / "domain" / "订单.ts").write_text(
                "import { Db } from '../infra/db';\n", encoding="utf-8")
            (root / "src" / "infra" / "db.ts").write_text("export const Db = 1;\n", encoding="utf-8")
            code, output = support.run_on_ansi_console(cb.main, ["--root", str(root)])
            json_code, json_output = support.run_on_ansi_console(cb.main, ["--root", str(root), "--json"])
        self.assertEqual((code, json_code), (1, 1))
        self.assertIn("src/domain/订单.ts", output)
        self.assertEqual(json.loads(json_output)["violations"][0]["file"], "src/domain/订单.ts")


if __name__ == "__main__":
    unittest.main()
