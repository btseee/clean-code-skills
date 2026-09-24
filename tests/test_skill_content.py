"""The shipped skill content keeps the shape the loaders and budgets depend on."""

import re
import unittest

import support
import check_boundaries
import detect_stack
from structure import roles as structure_roles

REFERENCES = support.SKILL_ROOT / "references"
LANGUAGE_HEADINGS = ["Names", "Functions And Types", "Errors", "Modules And Visibility",
                     "Placement", "Tests", "Layers", "Enforce", "Smells"]
FRAMEWORK_HEADINGS = ["Structure", "Roles", "Rules", "Layers", "Tests", "Enforce", "Smells"]
OPTIONAL_HEADINGS = {"Concurrency"}
PACK_TOKEN_BUDGET = 2000
CONTENTS_THRESHOLD = 300
# A controller may import a repository; a repository may not import a controller.
PERSISTENCE_LAYERS = {"infrastructure", "infra", "persistence", "adapters", "data"}
DELIVERY_LAYERS = {"ui", "delivery", "web", "api"}
ARCHITECTURE_BLOCK = re.compile(r"```clean-architecture\n.*?```", re.S)


def tokens(text: str) -> int:
    """The validator's estimate: words times four thirds."""
    return len(text.split()) * 4 // 3


def packs(kind: str) -> list:
    folder = REFERENCES / kind
    return sorted(folder.glob("*.md")) if folder.is_dir() else []


class PackTemplateTest(unittest.TestCase):
    def assert_template(self, path, required):
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        self.assertTrue(lines[0].startswith("# "), "a pack opens with its title")
        first = next(line for line in lines[1:] if line.strip())
        self.assertTrue(first.startswith("> Applies to:"), "the line after the title says what it applies to")
        headings = [line[3:].strip() for line in lines if line.startswith("## ")]
        self.assertEqual([heading for heading in headings if heading not in OPTIONAL_HEADINGS], required)
        self.assertLessEqual(tokens(text), PACK_TOKEN_BUDGET, "a pack stays within its token budget")
        layers = text.split("\n## Layers", 1)[1].split("\n")
        opening = next(line for line in layers[1:] if line.strip())
        self.assertIn("Applies only when", opening, "layer rules are conditional on a declaration")
        return text

    def test_language_packs_follow_their_template(self):
        for path in packs("languages"):
            with self.subTest(pack=path.name):
                self.assert_template(path, LANGUAGE_HEADINGS)

    def test_framework_packs_follow_their_template_and_declare_roles(self):
        for path in packs("frameworks"):
            with self.subTest(pack=path.name):
                text = self.assert_template(path, FRAMEWORK_HEADINGS)
                self.assertEqual(text.count("```clean-roles"), 1)
                self.assertTrue(structure_roles.parse_roles(text, path.name))

    def test_suggested_layers_put_persistence_before_delivery(self):
        for path in packs("languages") + packs("frameworks"):
            for block in ARCHITECTURE_BLOCK.findall(path.read_text(encoding="utf-8")):
                order = check_boundaries.parse_layering(block).order
                persistence = [order[name] for name in PERSISTENCE_LAYERS if name in order]
                delivery = [order[name] for name in DELIVERY_LAYERS if name in order]
                if persistence and delivery:
                    with self.subTest(pack=path.name):
                        self.assertLess(max(persistence), min(delivery))


class PackIndexTest(unittest.TestCase):
    def setUp(self):
        self.index = detect_stack.load_pack_index()

    def test_the_index_and_the_pack_files_agree(self):
        indexed = {path for paths in list(self.index.languages.values())
                   + list(self.index.frameworks.values()) for path in paths}
        on_disk = {f"{kind}/{path.name}" for kind in ("languages", "frameworks") for path in packs(kind)}
        self.assertEqual(indexed - on_disk, set(), "indexed packs that do not exist")
        self.assertEqual(on_disk - indexed, set(), "packs the index never routes to")

    def test_every_label_is_one_detection_can_report(self):
        self.assertEqual(set(self.index.languages) - detect_stack.EMITTABLE_LANGUAGES, set())
        self.assertEqual(set(self.index.frameworks) - detect_stack.EMITTABLE_FRAMEWORKS, set())
        for source, dropped in self.index.supersedes.items():
            self.assertIn(source, detect_stack.EMITTABLE_FRAMEWORKS)
            self.assertEqual(dropped - detect_stack.EMITTABLE_FRAMEWORKS, set())

    def test_the_generic_roles_parse(self):
        text = (REFERENCES / "framework-map.md").read_text(encoding="utf-8")
        self.assertTrue(structure_roles.parse_roles(text, "framework-map.md"))


class ReferenceNavigationTest(unittest.TestCase):
    def test_long_references_open_with_a_contents_list(self):
        for path in sorted(REFERENCES.glob("*.md")):
            lines = path.read_text(encoding="utf-8").split("\n")
            if len(lines) > CONTENTS_THRESHOLD:
                with self.subTest(reference=path.name):
                    self.assertIn("## Contents", [line.strip() for line in lines[:30]])


if __name__ == "__main__":
    unittest.main()
