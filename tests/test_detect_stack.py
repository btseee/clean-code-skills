import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import support  # puts the scripts folder on sys.path
import detect_stack

INDEX = """
Prose before the index.

```clean-packs
# comments are ignored
language TypeScript = languages/typescript.md, languages/javascript.md
language JavaScript = languages/javascript.md
language Shell = languages/shell.md
language C# = languages/csharp.md
framework Express = frameworks/express.md
framework NestJS = frameworks/nestjs.md
framework Next.js = frameworks/nextjs.md, frameworks/react.md
framework Ruby on Rails = frameworks/rails.md
supersede NestJS > Express
```
"""


def make_project(files: dict) -> tempfile.TemporaryDirectory:
    directory = tempfile.TemporaryDirectory()
    for path, text in files.items():
        target = Path(directory.name) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return directory


class PackIndexTest(unittest.TestCase):
    def test_statements_parse_into_labels_paths_and_supersedes(self):
        index = detect_stack.parse_pack_index(INDEX)
        self.assertEqual(index.languages["TypeScript"],
                         ["languages/typescript.md", "languages/javascript.md"])
        self.assertEqual(index.frameworks["Ruby on Rails"], ["frameworks/rails.md"])
        self.assertEqual(index.supersedes["NestJS"], {"Express"})

    def test_a_malformed_line_is_named(self):
        with self.assertRaises(ValueError) as raised:
            detect_stack.parse_pack_index("```clean-packs\nlanguage = x\n```\n")
        self.assertIn("language = x", str(raised.exception))

    def test_text_without_an_index_has_no_packs(self):
        index = detect_stack.parse_pack_index("nothing here")
        self.assertEqual((index.languages, index.frameworks), ({}, {}))


class SelectPacksTest(unittest.TestCase):
    def setUp(self):
        self.index = detect_stack.parse_pack_index(INDEX)

    def test_minor_languages_and_superseded_frameworks_are_left_out(self):
        packs = detect_stack.select_packs(
            {"TypeScript": 90, "JavaScript": 8, "Shell": 2}, ["Express", "NestJS"], self.index)
        self.assertEqual(packs, ["references/languages/typescript.md",
                                 "references/languages/javascript.md",
                                 "references/frameworks/nestjs.md"])

    def test_unindexed_languages_do_not_count(self):
        packs = detect_stack.select_packs({"SQL": 50, "C#": 40}, [], self.index)
        self.assertEqual(packs, ["references/languages/csharp.md"])

    def test_a_substantial_second_language_gets_its_pack(self):
        packs = detect_stack.select_packs({"TypeScript": 60, "Shell": 40}, [], self.index)
        self.assertIn("references/languages/shell.md", packs)

    def test_supersede_applies_only_within_the_manifests_that_show_both(self):
        index = detect_stack.parse_pack_index(
            "```clean-packs\nframework React = frameworks/react.md\n"
            "framework Strapi = frameworks/strapi.md\nsupersede Strapi > React\n```")
        frameworks = ["React", "Strapi"]
        cms_only = {"React": ["cms/package.json"], "Strapi": ["cms/package.json"]}
        self.assertEqual(detect_stack.select_packs({}, frameworks, index, cms_only),
                         ["references/frameworks/strapi.md"])
        with_web = {"React": ["cms/package.json", "web/package.json"],
                    "Strapi": ["cms/package.json"]}
        self.assertEqual(detect_stack.select_packs({}, frameworks, index, with_web),
                         ["references/frameworks/react.md", "references/frameworks/strapi.md"])

    def test_framework_packs_are_scoped_to_the_folders_of_their_manifests(self):
        index = detect_stack.parse_pack_index(
            "```clean-packs\nlanguage TypeScript = languages/typescript.md\n"
            "language Vue = frameworks/vue-nuxt.md\n"
            "framework React = frameworks/react.md\nframework Flutter = frameworks/flutter.md\n"
            "framework Express = frameworks/express.md\nframework Vue = frameworks/vue-nuxt.md\n```")
        evidence = {"React": ["web/package.json"], "Flutter": ["mobile/pubspec.yaml"],
                    "Express": ["package.json"], "Vue": ["admin/package.json"]}
        scopes = detect_stack.pack_scopes({"TypeScript": 50, "Vue": 40},
                                          ["Express", "Flutter", "React", "Vue"], index, evidence)
        self.assertEqual(scopes, {"references/frameworks/react.md": ["web"],
                                  "references/frameworks/flutter.md": ["mobile"]})

    def test_manifest_scan_records_which_manifest_showed_each_framework(self):
        with make_project({"cms/package.json": '{"dependencies": {"@strapi/strapi": "5", "react": "18"}}',
                           "web/package.json": '{"dependencies": {"react": "19"}}'}) as root:
            manifests = [{"path": "cms/package.json"}, {"path": "web/package.json"}]
            frameworks, _, evidence = detect_stack.scan_manifest_contents(Path(root), manifests)
        self.assertEqual(frameworks, ["React", "Strapi"])
        self.assertEqual(evidence, {"React": ["cms/package.json", "web/package.json"],
                                    "Strapi": ["cms/package.json"]})

    def test_framework_packs_that_build_on_another_keep_both(self):
        packs = detect_stack.select_packs({}, ["Next.js"], self.index)
        self.assertEqual(packs, ["references/frameworks/nextjs.md",
                                 "references/frameworks/react.md"])


class SignatureTest(unittest.TestCase):
    CASES = [
        ('{"devDependencies": {"@sveltejs/kit": "^2.0.0"}}', "SvelteKit"),
        ('{"dependencies": {"@strapi/strapi": "5.0.0"}}', "Strapi"),
        ('<Project Sdk="Microsoft.NET.Sdk.Web">', "ASP.NET Core"),
        ("implementation(libs.ktor.server.core)", "Ktor"),
        ('implementation("io.ktor:ktor-server-netty:3.0.0")', "Ktor"),
        ("require github.com/beego/beego/v2 v2.3.0", "Beego"),
        ("<groupId>org.springframework</groupId>", "Spring"),
        ('implementation("androidx.compose.ui:ui")', "Jetpack Compose"),
    ]

    def test_new_framework_signatures(self):
        for text, label in self.CASES:
            with self.subTest(label=label):
                self.assertIn(label, detect_stack.match_signatures(text, detect_stack.FRAMEWORK_MATCHERS))

    def test_swiftui_and_uikit_come_from_sources(self):
        directory = make_project({
            "App/ContentView.swift": "import SwiftUI\nstruct ContentView: View {}\n",
            "Legacy/Controller.m": "#import <UIKit/UIKit.h>\n",
            "Other/Model.swift": "import Foundation\n",
        })
        with directory:
            found = detect_stack.scan_source_signatures(
                Path(directory.name),
                ["App/ContentView.swift", "Legacy/Controller.m", "Other/Model.swift"])
        self.assertEqual(found, {"SwiftUI": ["App/ContentView.swift"],
                                 "UIKit": ["Legacy/Controller.m"]})

    def test_every_new_label_is_emittable(self):
        for label in ("SvelteKit", "Strapi", "Beego", "Spring", "Jetpack Compose", "Ktor",
                      "SwiftUI", "UIKit", "ASP.NET Core"):
            self.assertIn(label, detect_stack.EMITTABLE_FRAMEWORKS)
        self.assertIn("C#", detect_stack.EMITTABLE_LANGUAGES)


class BuildContextTest(unittest.TestCase):
    def test_packs_come_from_the_index(self):
        directory = make_project({
            "package.json": '{"dependencies": {"express": "4.19.2"}}\n',
            "src/index.ts": "export const x = 1;\n",
        })
        index = detect_stack.parse_pack_index(INDEX)
        with directory, mock.patch.object(detect_stack, "load_pack_index", return_value=index):
            context = detect_stack.build_context(Path(directory.name))
        self.assertEqual(context["packs"], ["references/languages/typescript.md",
                                            "references/languages/javascript.md",
                                            "references/frameworks/express.md"])
        self.assertIn("Read next", detect_stack.render_summary(context))

    def test_each_framework_pack_is_scoped_to_its_own_project_in_a_monorepo(self):
        directory = make_project({
            "web/package.json": '{"dependencies": {"react": "19.0.0"}}\n',
            "web/src/App.jsx": "export default function App() { return null; }\n",
            "ios/Package.swift": "// swift-tools-version:6.0\n",
            "ios/Sources/App/ContentView.swift": "import SwiftUI\nstruct ContentView: View {}\n",
        })
        with directory:
            context = detect_stack.build_context(Path(directory.name))
        self.assertEqual(context["pack_scopes"], {
            "references/frameworks/react.md": ["web"],
            "references/frameworks/swiftui-uikit.md": ["ios"],
        })

    def test_a_missing_index_means_no_packs_and_a_note(self):
        directory = make_project({"src/index.ts": "export const x = 1;\n"})
        with directory, mock.patch.object(detect_stack, "PACK_INDEX_PATH",
                                          Path(directory.name) / "missing.md"):
            context = detect_stack.build_context(Path(directory.name))
        self.assertEqual(context["packs"], [])
        self.assertIn("packs_note", context)

    def test_write_merges_instead_of_clobbering(self):
        directory = make_project({
            ".clean/context.json": '{"confirmed": {"purpose": "demo"}, "future_key": 123}\n',
            "package.json": '{"name": "x", "dependencies": {"react": "18.3.1"}}\n',
            "src/index.js": "const x = 1;\n",
        })
        with directory:
            root = Path(directory.name)
            with mock.patch("sys.stdout"):
                detect_stack.main(["--root", str(root), "--write"])
            data = json.loads((root / ".clean" / "context.json").read_text(encoding="utf-8"))
        self.assertEqual(data["confirmed"]["purpose"], "demo")
        self.assertEqual(data["future_key"], 123)
        self.assertTrue(data["primary_language"])
        self.assertIn("packs", data)

    def test_json_reaches_a_console_that_cannot_encode_a_folder_name(self):
        directory = make_project({
            "网站/package.json": '{"name": "x", "dependencies": {"react": "18.3.1"}}\n',
            "网站/src/index.js": "const x = 1;\n",
        })
        with directory:
            code, output = support.run_on_ansi_console(
                detect_stack.main, ["--root", directory.name, "--json"])
        self.assertEqual(code, 0)
        self.assertIn("网站", json.dumps(json.loads(output), ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
