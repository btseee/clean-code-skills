import unittest

import support  # noqa: F401  (puts the scripts folder on sys.path)
from structure import metrics as component_metrics


def by_name(result):
    return {component["name"]: component for component in result["components"]}


class ComponentOfTest(unittest.TestCase):
    def test_components_are_folder_prefixes(self):
        self.assertEqual(component_metrics.component_of("src/services/auth.ts", 2), "src/services")
        self.assertEqual(component_metrics.component_of("src/services/deep/auth.ts", 2), "src/services")
        self.assertEqual(component_metrics.component_of("src/index.ts", 2), "src")
        self.assertEqual(component_metrics.component_of("main.go", 2), ".")


class AnalyzeTest(unittest.TestCase):
    def test_coupling_and_instability(self):
        result = component_metrics.analyze(
            {"a/x/1.ts": ["b/y/1.ts"], "b/y/1.ts": ["c/z/1.ts"], "c/z/1.ts": []}, {}, 2)
        middle = by_name(result)["b/y"]
        self.assertEqual((middle["ca"], middle["ce"], middle["instability"]), (1, 1, 0.5))
        self.assertEqual(by_name(result)["a/x"]["instability"], 1.0)
        self.assertEqual(by_name(result)["c/z"]["instability"], 0.0)

    def test_abstractness_and_distance_need_types(self):
        result = component_metrics.analyze(
            {"a/x/1.ts": ["b/y/1.ts"], "b/y/1.ts": ["c/z/1.ts"], "c/z/1.ts": []},
            {"b/y/1.ts": (2, 1)}, 2)
        middle = by_name(result)["b/y"]
        self.assertEqual((middle["abstractness"], middle["distance"]), (0.5, 0.0))
        self.assertIsNone(by_name(result)["a/x"]["abstractness"])
        self.assertIsNone(by_name(result)["a/x"]["distance"])

    def test_a_component_nobody_touches_has_no_instability(self):
        result = component_metrics.analyze({"lonely/x/1.ts": []}, {}, 2)
        self.assertIsNone(by_name(result)["lonely/x"]["instability"])

    def test_cycles_are_reported_once(self):
        result = component_metrics.analyze(
            {"a/1.ts": ["b/1.ts"], "b/1.ts": ["a/1.ts"], "c/1.ts": ["a/1.ts"]}, {}, 1)
        self.assertEqual(len(result["cycles"]), 1)
        self.assertEqual(result["cycles"][0]["components"], ["a", "b"])
        self.assertEqual(len(result["cycles"][0]["edges"]), 2)

    def test_imports_inside_one_component_are_not_edges(self):
        result = component_metrics.analyze({"a/x/1.ts": ["a/x/2.ts"], "a/x/2.ts": []}, {}, 2)
        self.assertEqual(result["edges"], [])

    def test_edges_count_import_pairs(self):
        result = component_metrics.analyze(
            {"a/1.ts": ["b/1.ts", "b/2.ts"], "a/2.ts": ["b/1.ts"], "b/1.ts": [], "b/2.ts": []}, {}, 1)
        self.assertEqual(result["edges"], [{"from": "a", "to": "b", "count": 3}])


if __name__ == "__main__":
    unittest.main()
