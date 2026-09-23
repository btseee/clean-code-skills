#!/usr/bin/env python3
"""Detect a project's stack, layout, and verification commands.

Answers the questions an agent must know before editing code it has never seen:
which languages and frameworks are in play, which packs to read for them, where
source and tests live, what command proves a change, and which directories look
like architectural layers.

Writes the result to .clean/context.json so a later session, or an agent with
no memory of this one, can read the answers instead of re-deriving them.

Standard library only. Reads files; writes nothing unless --write is given.

Usage:
    python detect_stack.py                # human-readable summary
    python detect_stack.py --json         # machine-readable, for tools
    python detect_stack.py --write        # also save .clean/context.json
    python detect_stack.py --root ../app  # inspect a different directory
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple, Optional

import project_files
from project_files import TEST_DIR_NAMES, TEST_FILE_PATTERN, is_skippable

SCHEMA_VERSION = 1

# Extension -> language. Deliberately broad: the skill must work in any language,
# so an unknown extension is reported as unknown rather than forced into a guess.
LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".cs": "C#", ".fs": "F#", ".fsx": "F#", ".vb": "Visual Basic",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".swift": "Swift", ".m": "Objective-C", ".mm": "Objective-C++",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++",
    ".hpp": "C++ header", ".hh": "C++ header",
    ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".clj": "Clojure", ".cljs": "ClojureScript", ".hs": "Haskell", ".ml": "OCaml",
    ".lua": "Lua", ".pl": "Perl", ".pm": "Perl", ".r": "R", ".jl": "Julia",
    ".zig": "Zig", ".nim": "Nim", ".cr": "Crystal", ".sol": "Solidity",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".sql": "SQL", ".graphql": "GraphQL", ".gql": "GraphQL",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".tf": "Terraform", ".bicep": "Bicep",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less",
    ".html": "HTML", ".htm": "HTML",
}

# Manifest filename -> (ecosystem, canonical verify command).
# The command is a starting point the agent must confirm, not a guarantee.
MANIFESTS = {
    "package.json": ("Node.js", "npm test"),
    "deno.json": ("Deno", "deno test"),
    "pyproject.toml": ("Python", "pytest"),
    "setup.py": ("Python", "pytest"),
    "setup.cfg": ("Python", "pytest"),
    "requirements.txt": ("Python", "pytest"),
    "Pipfile": ("Python", "pipenv run pytest"),
    "go.mod": ("Go", "go test ./..."),
    "Cargo.toml": ("Rust", "cargo test"),
    "pom.xml": ("Java/Maven", "mvn test"),
    "build.gradle": ("Java/Gradle", "gradle test"),
    "build.gradle.kts": ("Kotlin/Gradle", "gradle test"),
    "Gemfile": ("Ruby", "bundle exec rspec"),
    "composer.json": ("PHP", "vendor/bin/phpunit"),
    "mix.exs": ("Elixir", "mix test"),
    "rebar.config": ("Erlang", "rebar3 eunit"),
    "Package.swift": ("Swift", "swift test"),
    "pubspec.yaml": ("Dart/Flutter", "dart test"),
    "libs.versions.toml": ("Gradle version catalog", "gradle test"),
    "CMakeLists.txt": ("C/C++ (CMake)", "ctest"),
    "Makefile": ("Make", "make test"),
    "build.zig": ("Zig", "zig build test"),
    "shard.yml": ("Crystal", "crystal spec"),
    "dune-project": ("OCaml", "dune test"),
    "stack.yaml": ("Haskell", "stack test"),
    "cabal.project": ("Haskell", "cabal test"),
    "Project.toml": ("Julia", "julia --project -e 'using Pkg; Pkg.test()'"),
    "DESCRIPTION": ("R", "R CMD check ."),
}

# Manifests identified by extension rather than exact name.
MANIFEST_SUFFIXES = {
    ".csproj": ("C#/.NET", "dotnet test"),
    ".fsproj": ("F#/.NET", "dotnet test"),
    ".vbproj": ("Visual Basic/.NET", "dotnet test"),
    ".sln": (".NET solution", "dotnet test"),
    ".slnx": (".NET solution", "dotnet test"),
}

# Dependency name fragment -> framework label. Matched against manifest text, so
# one table serves every ecosystem's manifest format.
FRAMEWORK_SIGNATURES = [
    ("react", "React"), ("next", "Next.js"), ("vue", "Vue"), ("nuxt", "Nuxt"),
    ("@angular/core", "Angular"), ("svelte", "Svelte"), ("@sveltejs/kit", "SvelteKit"),
    ("solid-js", "SolidJS"),
    ("express", "Express"), ("fastify", "Fastify"), ("nestjs", "NestJS"),
    ("@nestjs/core", "NestJS"), ("hono", "Hono"), ("@strapi/strapi", "Strapi"),
    ("django", "Django"), ("flask", "Flask"), ("fastapi", "FastAPI"),
    ("sqlalchemy", "SQLAlchemy"), ("pydantic", "Pydantic"), ("celery", "Celery"),
    ("spring-boot", "Spring Boot"), ("org.springframework", "Spring"),
    ("quarkus", "Quarkus"), ("micronaut", "Micronaut"),
    ("microsoft.aspnetcore", "ASP.NET Core"), ("microsoft.net.sdk.web", "ASP.NET Core"),
    ("microsoft.entityframeworkcore", "EF Core"),
    ("akka", "Akka"), ("mediatr", "MediatR"), ("dapper", "Dapper"),
    ("rails", "Ruby on Rails"), ("sinatra", "Sinatra"),
    ("laravel", "Laravel"), ("symfony", "Symfony"),
    ("gin-gonic", "Gin"), ("beego", "Beego"), ("gofiber/fiber", "Fiber"),
    ("labstack/echo", "Echo"),
    ("actix", "Actix"), ("axum", "Axum"), ("rocket", "Rocket"), ("tokio", "Tokio"),
    ("phoenix", "Phoenix"), ("flutter", "Flutter"),
    ("androidx.compose", "Jetpack Compose"), ("io.ktor", "Ktor"), ("ktor-server", "Ktor"),
    ("ktor.server", "Ktor"),
    ("tensorflow", "TensorFlow"), ("torch", "PyTorch"), ("pandas", "pandas"),
]

# Frameworks that no manifest names: Apple's UI frameworks ship with the platform,
# so only the sources' imports reveal them. (suffixes, pattern, label)
SOURCE_FRAMEWORK_SIGNATURES = (
    ((".swift",), re.compile(r"^[ \t]*import[ \t]+SwiftUI\b", re.M), "SwiftUI"),
    ((".swift",), re.compile(r"^[ \t]*import[ \t]+UIKit\b", re.M), "UIKit"),
    ((".m", ".mm", ".h"), re.compile(r"^[ \t]*(?:#import[ \t]*<UIKit/|@import[ \t]+UIKit\b)", re.M),
     "UIKit"),
)
SOURCE_SCAN_FILES = 200
SOURCE_SCAN_LINES = 60

# Dependency name fragment -> test runner label.
TEST_RUNNER_SIGNATURES = [
    ("vitest", "Vitest"), ("jest", "Jest"), ("mocha", "Mocha"), ("jasmine", "Jasmine"),
    ("playwright", "Playwright"), ("cypress", "Cypress"),
    ("pytest", "pytest"), ("unittest2", "unittest"), ("nose", "nose"),
    ("xunit", "xUnit"), ("nunit", "NUnit"), ("mstest", "MSTest"),
    ("junit", "JUnit"), ("testng", "TestNG"), ("spock", "Spock"),
    ("rspec", "RSpec"), ("minitest", "Minitest"),
    ("phpunit", "PHPUnit"), ("pest", "Pest"),
    ("testify", "Testify"), ("ginkgo", "Ginkgo"),
]

# Directory name -> the architectural role it conventionally signals. Used to
# offer a starting layer map; the project's real layout always overrides it.
LAYER_HINTS = {
    "domain": "domain", "entities": "domain", "entity": "domain", "model": "domain",
    "models": "domain", "core": "domain", "business": "domain",
    "usecases": "application", "use_cases": "application", "application": "application",
    "services": "application", "handlers": "application",
    "commands": "application", "queries": "application", "features": "application",
    "adapters": "adapter", "controllers": "adapter", "api": "adapter",
    "presentation": "adapter", "ui": "adapter", "views": "adapter", "web": "adapter",
    "graphql": "adapter", "rest": "adapter", "cli": "adapter",
    "infrastructure": "infrastructure", "infra": "infrastructure", "persistence": "infrastructure",
    "repositories": "infrastructure", "repository": "infrastructure", "data": "infrastructure",
    "db": "infrastructure", "database": "infrastructure", "gateways": "infrastructure",
    "clients": "infrastructure", "external": "infrastructure",
}

SOURCE_DIR_NAMES = frozenset({"src", "lib", "source", "sources", "app", "pkg", "internal"})

QUALITY_TOOL_FILES = {
    ".editorconfig": "EditorConfig",
    ".eslintrc": "ESLint", ".eslintrc.json": "ESLint", ".eslintrc.js": "ESLint",
    "eslint.config.js": "ESLint", "eslint.config.mjs": "ESLint",
    ".prettierrc": "Prettier", "prettier.config.js": "Prettier",
    "biome.json": "Biome", ".ruff.toml": "Ruff", "ruff.toml": "Ruff",
    ".flake8": "Flake8", "mypy.ini": "mypy", ".pylintrc": "Pylint",
    ".rubocop.yml": "RuboCop", ".golangci.yml": "golangci-lint",
    ".golangci.yaml": "golangci-lint", "rustfmt.toml": "rustfmt",
    "clippy.toml": "Clippy", ".clang-format": "clang-format",
    "checkstyle.xml": "Checkstyle", "spotbugs.xml": "SpotBugs",
    ".stylecop.json": "StyleCop", "Directory.Build.props": "MSBuild shared props",
    ".pre-commit-config.yaml": "pre-commit", "lefthook.yml": "Lefthook",
    "dependency-cruiser.js": "dependency-cruiser",
    ".dependency-cruiser.js": "dependency-cruiser",
    ".importlinter": "import-linter",
}

# Many projects configure their formatter, linter and test runner inside a manifest
# rather than as a standalone dotfile -- pyproject.toml [tool.ruff], package.json
# "eslintConfig", setup.cfg [flake8]. Looking only for files reports "no quality
# tools" on a project that has four of them, which invites an agent to hand-format.
QUALITY_TOOL_MARKERS = {
    "pyproject.toml": {
        "[tool.black]": "Black", "[tool.ruff": "Ruff", "[tool.isort]": "isort",
        "[tool.mypy]": "mypy", "[tool.pytest": "pytest", "[tool.flake8]": "Flake8",
        "[tool.pylint": "Pylint", "[tool.coverage": "coverage",
    },
    "setup.cfg": {"[flake8]": "Flake8", "[mypy]": "mypy", "[tool:pytest]": "pytest"},
    "package.json": {
        '"eslintConfig"': "ESLint", '"prettier"': "Prettier",
        '"jest"': "Jest", '"biome"': "Biome",
    },
    "Cargo.toml": {"[lints": "Cargo lints"},
    "composer.json": {'"phpstan"': "PHPStan", '"php-cs-fixer"': "PHP-CS-Fixer"},
}

AGENT_CONTEXT_FILES = (
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "CONTRIBUTING.md",
    ".github/copilot-instructions.md", ".cursor/rules", ".windsurf/rules",
    "ARCHITECTURE.md", "docs/architecture.md", "adr", "docs/adr",
)

MANIFEST_READ_LIMIT = 200_000


def read_text_safely(path: Path, limit: int = MANIFEST_READ_LIMIT) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def count_languages(files) -> dict:
    counts: dict = {}
    for relative_path, _ in files:
        language = LANGUAGE_BY_EXTENSION.get(relative_path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def find_manifests(root: Path, files) -> list:
    found = []
    for relative_path, filename in files:
        entry = MANIFESTS.get(filename)
        if entry is None:
            entry = MANIFEST_SUFFIXES.get(relative_path.suffix.lower())
        if entry is None:
            continue
        ecosystem, verify_command = entry
        found.append({
            "path": relative_path.as_posix(),
            "ecosystem": ecosystem,
            "suggested_verify_command": verify_command,
            "depth": len(relative_path.parts) - 1,
        })
    found.sort(key=lambda item: (item["depth"], item["path"]))
    return found


COMMENT_PATTERNS = (
    re.compile(r"<!--.*?-->", re.DOTALL),      # XML: csproj, pom.xml
    re.compile(r"/\*.*?\*/", re.DOTALL),       # C-style block comments
    re.compile(r"(?m)^[ \t]*//.*$"),           # line comments, but not URLs mid-line
    re.compile(r"(?m)^[ \t]*#.*$"),            # TOML, YAML, requirements.txt
)


def strip_comments(text: str) -> str:
    """Remove comment bodies so prose cannot be mistaken for a dependency.

    A .csproj comment containing the English word "next" was enough to report a
    .NET service as using Next.js. Dependency detection must read declarations,
    not commentary.
    """
    for pattern in COMMENT_PATTERNS:
        text = pattern.sub(" ", text)
    return text


def compile_signatures(signatures) -> list:
    """Require a non-alphanumeric boundary around each name.

    Bare substring matching is wrong here: "ava" would match "javascript" and
    "next" would match "nextgen", so a .NET project could be reported as using
    Next.js. Dots, hyphens, quotes and angle brackets all count as boundaries,
    which is what separates a dependency name in JSON, XML, TOML and YAML alike.
    """
    return [
        (re.compile(r"(?<![a-z0-9])" + re.escape(fragment) + r"(?![a-z0-9])"), label)
        for fragment, label in signatures
    ]


FRAMEWORK_MATCHERS = compile_signatures(FRAMEWORK_SIGNATURES)
TEST_RUNNER_MATCHERS = compile_signatures(TEST_RUNNER_SIGNATURES)


def match_signatures(text: str, matchers) -> list:
    lowered = text.lower()
    return sorted({label for pattern, label in matchers if pattern.search(lowered)})


def scan_manifest_contents(root: Path, manifests: list) -> tuple:
    """Frameworks and test runners the manifests name, and which manifests named each framework."""
    evidence: dict = {}
    test_runners: set = set()
    for manifest in manifests[:40]:
        text = read_text_safely(root / manifest["path"])
        if not text:
            continue
        text = strip_comments(text)
        for label in match_signatures(text, FRAMEWORK_MATCHERS):
            evidence.setdefault(label, []).append(manifest["path"])
        test_runners.update(match_signatures(text, TEST_RUNNER_MATCHERS))
    return sorted(evidence), sorted(test_runners), {label: sorted(paths) for label, paths in evidence.items()}


def scan_source_signatures(root: Path, relative_paths) -> dict:
    """Frameworks revealed only by imports in the sources, each with the file that showed it."""
    found = {}
    for suffixes, pattern, label in SOURCE_FRAMEWORK_SIGNATURES:
        candidates = [path for path in relative_paths if path.lower().endswith(suffixes)]
        for relative in candidates[:SOURCE_SCAN_FILES]:
            text = project_files.read_text(root / relative)
            if text and pattern.search("\n".join(text.split("\n", SOURCE_SCAN_LINES)[:SOURCE_SCAN_LINES])):
                found[label] = [relative]
                break
    return found


def enclosing_manifests(paths, manifests) -> list:
    """For each source path, the nearest manifest whose folder contains it."""
    found = []
    for path in paths:
        owners = [manifest["path"] for manifest in manifests
                  if "/" not in manifest["path"]
                  or path.startswith(manifest["path"].rpartition("/")[0] + "/")]
        if owners:
            found.append(max(owners, key=lambda owner: owner.count("/")))
    return found


# --- packs: which references/ files the detected stack needs -------------------------

PACK_INDEX_PATH = Path(__file__).resolve().parent.parent / "references" / "framework-map.md"
PACKS_BLOCK_PATTERN = re.compile(r"```clean-packs[ \t]*\n(.*?)```", re.DOTALL)
PACK_LINE_PATTERN = re.compile(r"^(language|framework)[ \t]+(.+?)[ \t]*=[ \t]*(.+)$")
SUPERSEDE_LINE_PATTERN = re.compile(r"^supersede[ \t]+(.+?)[ \t]*>[ \t]*(.+)$")
# A language covering less than this share of the indexed files gets no pack of its
# own: a few build scripts do not make a TypeScript project a Shell project.
MINOR_LANGUAGE_SHARE = 0.10

EMITTABLE_LANGUAGES = frozenset(LANGUAGE_BY_EXTENSION.values())
EMITTABLE_FRAMEWORKS = frozenset(
    [label for _, label in FRAMEWORK_SIGNATURES]
    + [label for _, _, label in SOURCE_FRAMEWORK_SIGNATURES]
)


class PackIndex(NamedTuple):
    languages: dict
    frameworks: dict
    supersedes: dict


def _split_list(raw: str) -> list:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_pack_index(text: str) -> PackIndex:
    """The clean-packs block in text; empty when there is none."""
    index = PackIndex({}, {}, {})
    match = PACKS_BLOCK_PATTERN.search(text)
    if match is None:
        return index
    for raw in match.group(1).split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pack = PACK_LINE_PATTERN.match(line)
        if pack:
            kind, label, paths = pack.groups()
            target = index.languages if kind == "language" else index.frameworks
            target[label.strip()] = _split_list(paths)
            continue
        supersede = SUPERSEDE_LINE_PATTERN.match(line)
        if supersede:
            index.supersedes.setdefault(supersede.group(1).strip(), set()).update(
                _split_list(supersede.group(2)))
            continue
        raise ValueError(f"pack index: cannot parse {line!r}")
    return index


def load_pack_index(path: Path = None) -> Optional[PackIndex]:
    path = path or PACK_INDEX_PATH
    if not path.is_file():
        return None
    return parse_pack_index(read_text_safely(path, limit=1_000_000))


def _superseded(framework: str, frameworks, index: PackIndex, evidence) -> bool:
    """A framework drops out only where a framework that covers it shows up too.

    Strapi's admin panel puts React in every Strapi manifest; a React app with its own
    manifest beside the CMS keeps the React pack.
    """
    covering = [other for other in frameworks if framework in index.supersedes.get(other, ())]
    if not covering:
        return False
    if evidence is None or not evidence.get(framework):
        return True
    return all(any(path in evidence.get(other, ()) for other in covering)
               for path in evidence[framework])


def pack_scopes(languages: dict, frameworks, index: PackIndex, evidence) -> dict:
    """The folders each framework pack's role conventions apply to: where its manifests are.

    Packs a language reaches, or a manifest at the root, apply everywhere and are left out.
    """
    everywhere = set(select_packs(languages, [], index))
    folders: dict = {}
    for framework in frameworks:
        where = {path.rpartition("/")[0] for path in evidence.get(framework, [])} or {""}
        for pack in index.frameworks.get(framework, []):
            folders.setdefault("references/" + pack, set()).update(where)
    return {pack: sorted(where) for pack, where in folders.items()
            if pack not in everywhere and "" not in where}


def select_packs(languages: dict, frameworks, index: PackIndex, evidence=None) -> list:
    """Pack paths for a stack: its main languages, then its frameworks, each once."""
    indexed = [(label, count) for label, count in languages.items() if label in index.languages]
    chosen = []
    if indexed:
        total = sum(count for _, count in indexed)
        top = max(indexed, key=lambda item: item[1])[0]
        chosen = [label for label, count in indexed
                  if label == top or count / total >= MINOR_LANGUAGE_SHARE]
    dropped = {framework for framework in frameworks
               if _superseded(framework, frameworks, index, evidence)}
    paths = [path for label in chosen for path in index.languages[label]]
    paths += [path for framework in frameworks
              if framework in index.frameworks and framework not in dropped
              for path in index.frameworks[framework]]
    unique = []
    for path in paths:
        if path not in unique:
            unique.append(path)
    return ["references/" + path for path in unique]


MAX_DEPENDENCIES = 120

DEPENDENCY_LINE_PARSERS = {
    # requirements.txt: "fastapi==0.111.0", "requests>=2.31", bare "ruff"
    "requirements.txt": re.compile(
        r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:(?:==|>=|<=|~=|!=|>|<)\s*([^\s;#]+))?"
    ),
    # go.mod require lines: "github.com/gin-gonic/gin v1.9.1"
    "go.mod": re.compile(r"^\s*([A-Za-z0-9._/\-]+\.[A-Za-z0-9._/\-]+)\s+(v[\w.\-+]+)"),
    # Gemfile: gem "rails", "~> 7.1"
    "Gemfile": re.compile(r"""^\s*gem\s+['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]+)['"])?"""),
}

CSPROJ_PACKAGE_PATTERN = re.compile(
    r"""<PackageReference\s+[^>]*Include\s*=\s*"([^"]+)"[^>]*?(?:Version\s*=\s*"([^"]+)")?""",
    re.IGNORECASE,
)
# .NET Central Package Management: versions live in Directory.Packages.props, and the
# csproj carries only the name. Without this, every version on such a solution is blank.
PACKAGE_VERSION_PATTERN = re.compile(
    r"""<PackageVersion\s+[^>]*Include\s*=\s*"([^"]+)"[^>]*Version\s*=\s*"([^"]+)\"""",
    re.IGNORECASE,
)


def central_package_versions(root: Path) -> dict:
    versions: dict = {}
    candidates = [root / "Directory.Packages.props"]
    try:
        candidates.extend(sorted(root.glob("*/Directory.Packages.props"))[:5])
    except OSError:
        pass
    for path in candidates:
        if not path.is_file():
            continue
        for name, version in PACKAGE_VERSION_PATTERN.findall(read_text_safely(path)):
            versions.setdefault(name.lower(), version)
    return versions
TOML_SECTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*$")
TOML_KEY_VALUE_PATTERN = re.compile(r"""^\s*([A-Za-z0-9._\-"]+)\s*=\s*(.+?)\s*(?:#.*)?$""")
PEP508_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:(?:==|>=|<=|~=|!=|>|<)\s*([^\s;,]+))?"
)


def parse_json_dependencies(text: str, keys) -> list:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    found = []
    for key in keys:
        section = data.get(key)
        if isinstance(section, dict):
            found.extend(
                {"name": name, "version": str(version)}
                for name, version in section.items()
            )
    return found


def parse_toml_table_dependencies(text: str, table_names) -> list:
    """Read `name = "version"` pairs from named TOML tables, standard library only.

    tomllib exists from 3.11, but the scripts promise 3.8 -- and dependency tables are
    flat enough that a line parser is honest about what it can and cannot read.
    """
    found = []
    current = None
    for line in text.splitlines():
        section = TOML_SECTION_PATTERN.match(line)
        if section:
            current = section.group(1).strip()
            continue
        if current not in table_names:
            continue
        pair = TOML_KEY_VALUE_PATTERN.match(line)
        if not pair:
            continue
        name = pair.group(1).strip('"')
        value = pair.group(2).strip()
        version = ""
        if value.startswith('"'):
            version = value.strip('"')
        else:
            embedded = re.search(r'version\s*=\s*"([^"]+)"', value)
            if embedded:
                version = embedded.group(1)
        found.append({"name": name, "version": version})
    return found


def parse_pyproject_dependencies(text: str) -> list:
    """PEP 621 `[project] dependencies = [...]` entries, one string each."""
    found = []
    in_project = False
    in_list = False
    for line in text.splitlines():
        section = TOML_SECTION_PATTERN.match(line)
        if section:
            in_project = section.group(1).strip() == "project"
            in_list = False
            continue
        if not in_project:
            continue
        if re.match(r"^\s*dependencies\s*=\s*\[", line):
            in_list = True
        if not in_list:
            continue
        for spec in re.findall(r'"([^"]+)"', line):
            match = PEP508_PATTERN.match(spec)
            if match:
                found.append({"name": match.group(1), "version": match.group(2) or ""})
        if "]" in line:
            in_list = False
    return found


def parse_line_dependencies(text: str, pattern: re.Pattern) -> list:
    found = []
    in_require_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "-")):
            continue
        # go.mod groups requirements in a `require ( ... )` block.
        if stripped.startswith("require ("):
            in_require_block = True
            continue
        if in_require_block and stripped == ")":
            in_require_block = False
            continue
        match = pattern.match(line)
        if match and match.group(1):
            found.append({"name": match.group(1), "version": match.group(2) or ""})
    return found


def parse_dependencies(root: Path, manifests: list) -> list:
    """Collect declared dependencies with their versions, per manifest.

    The point is that an agent verifies API usage against the versions actually in
    use, instead of against its memory of some other version. Only declarations are
    read; lockfiles and transitive graphs are out of scope on purpose.
    """
    dependencies = []
    central_versions = None
    for manifest in manifests[:25]:
        path = manifest["path"]
        filename = Path(path).name
        text = read_text_safely(root / path)
        if not text:
            continue

        if filename == "package.json":
            entries = parse_json_dependencies(text, ("dependencies", "devDependencies"))
        elif filename == "composer.json":
            entries = parse_json_dependencies(text, ("require", "require-dev"))
        elif filename == "pyproject.toml":
            entries = parse_pyproject_dependencies(text)
        elif filename == "Cargo.toml":
            entries = parse_toml_table_dependencies(
                text, {"dependencies", "dev-dependencies", "build-dependencies"}
            )
        elif filename in DEPENDENCY_LINE_PARSERS:
            entries = parse_line_dependencies(text, DEPENDENCY_LINE_PARSERS[filename])
        elif Path(path).suffix.lower() in {".csproj", ".fsproj", ".vbproj"}:
            if central_versions is None:
                central_versions = central_package_versions(root)
            entries = [
                {
                    "name": name,
                    "version": version or central_versions.get(name.lower(), ""),
                }
                for name, version in CSPROJ_PACKAGE_PATTERN.findall(text)
            ]
        else:
            continue

        for entry in entries:
            entry["manifest"] = path
        dependencies.extend(entries)
        if len(dependencies) >= MAX_DEPENDENCIES:
            break

    seen = set()
    unique = []
    for entry in dependencies[:MAX_DEPENDENCIES]:
        key = (entry["name"].lower(), entry["manifest"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def find_test_locations(files) -> dict:
    directories: set = set()
    test_file_count = 0
    for relative_path, filename in files:
        parts = relative_path.parts
        in_test_dir = any(part.lower() in TEST_DIR_NAMES for part in parts[:-1])
        looks_like_test = bool(TEST_FILE_PATTERN.search(filename))
        if in_test_dir or looks_like_test:
            if relative_path.suffix.lower() in LANGUAGE_BY_EXTENSION:
                test_file_count += 1
                if len(parts) > 1:
                    directories.add(Path(*parts[:-1]).as_posix())
    return {
        "test_file_count": test_file_count,
        "test_directories": sorted(directories)[:25],
    }


def find_source_roots(root: Path) -> list:
    roots = []
    try:
        entries = sorted(entry for entry in root.iterdir() if entry.is_dir())
    except OSError:
        return roots
    for entry in entries:
        if is_skippable(entry.name):
            continue
        if entry.name.lower() in SOURCE_DIR_NAMES:
            roots.append(entry.name)
    return roots


def infer_layers(files) -> dict:
    """Map conventional directory names to architectural roles, with evidence."""
    layers: dict = {}
    for relative_path, _ in files:
        if relative_path.suffix.lower() not in LANGUAGE_BY_EXTENSION:
            continue
        for part in relative_path.parts[:-1]:
            role = LAYER_HINTS.get(part.lower())
            if role is None:
                continue
            bucket = layers.setdefault(role, {})
            bucket[part] = bucket.get(part, 0) + 1
    return {
        role: dict(sorted(names.items(), key=lambda item: (-item[1], item[0]))[:6])
        for role, names in sorted(layers.items())
    }


def find_quality_tools(root: Path, files) -> list:
    tools = set()
    manifests_seen = set()
    for relative_path, filename in files:
        label = QUALITY_TOOL_FILES.get(filename)
        if label:
            tools.add(label)
        if filename in QUALITY_TOOL_MARKERS and len(relative_path.parts) <= 2:
            manifests_seen.add((filename, relative_path))

    for filename, relative_path in manifests_seen:
        text = read_text_safely(root / relative_path)
        if not text:
            continue
        lowered = text.lower()
        for marker, label in QUALITY_TOOL_MARKERS[filename].items():
            if marker.lower() in lowered:
                tools.add(label)
    return sorted(tools)


def find_existing_context_files(root: Path) -> list:
    return [name for name in AGENT_CONTEXT_FILES if (root / name).exists()]


def infer_purpose(root: Path, manifests: list, languages: dict, tests: dict) -> dict:
    """Guess what kind of thing this project is. Reported as a guess, never a fact."""
    signals = []
    manifest_names = {Path(item["path"]).name for item in manifests}

    if len([m for m in manifests if m["depth"] <= 2]) > 3:
        signals.append("monorepo or multi-project solution")
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        signals.append("containerized deployment")
    if any((root / name).exists() for name in ("openapi.yaml", "openapi.json", "swagger.json")):
        signals.append("HTTP API with a published contract")
    if (root / ".github" / "workflows").is_dir():
        signals.append("CI configured")
    if "package.json" in manifest_names:
        package_text = read_text_safely(root / "package.json").lower()
        if '"bin"' in package_text:
            signals.append("ships a CLI")
        if '"private": true' not in package_text and '"version"' in package_text:
            signals.append("publishable package")
    if tests["test_file_count"] == 0:
        signals.append("no tests detected: treat every change as higher risk")

    return {
        "signals": signals,
        "note": "Purpose is inferred from layout only. Confirm it with the user "
                "before letting it influence a design decision.",
    }


def build_context(root: Path) -> dict:
    walk = project_files.walk(root)
    files = [(Path(relative), Path(relative).name) for relative in walk.paths]
    languages = count_languages(files)
    manifests = find_manifests(root, files)
    frameworks, test_runners, framework_evidence = scan_manifest_contents(root, manifests)
    for label, paths in scan_source_signatures(root, walk.paths).items():
        framework_evidence.setdefault(label, []).extend(enclosing_manifests(paths, manifests))
    frameworks = sorted(set(frameworks) | set(framework_evidence))
    tests = find_test_locations(files)
    pack_index = load_pack_index()

    primary_language = next(iter(languages), None)
    verify_commands = []
    for manifest in manifests:
        command = manifest["suggested_verify_command"]
        if command not in verify_commands:
            verify_commands.append(command)

    context = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "clean-code skill / detect_stack.py",
        "root": str(root),
        "confidence": "inferred from file layout; verify before relying on it",
        "primary_language": primary_language,
        "languages": languages,
        "ecosystems": sorted({item["ecosystem"] for item in manifests}),
        "manifests": manifests[:25],
        "frameworks": frameworks,
        "packs": select_packs(languages, frameworks, pack_index, framework_evidence) if pack_index else [],
        "pack_scopes": (pack_scopes(languages, frameworks, pack_index, framework_evidence)
                        if pack_index else {}),
        "test_runners": test_runners,
        "tests": tests,
        "dependencies": parse_dependencies(root, manifests),
        "suggested_verify_commands": verify_commands[:8],
        "source_roots": find_source_roots(root),
        "layer_candidates": infer_layers(files),
        "quality_tools": find_quality_tools(root, files),
        "existing_context_files": find_existing_context_files(root),
        "purpose": infer_purpose(root, manifests, languages, tests),
        "files_scanned": len(files),
        "scan_truncated": walk.truncated,
    }
    if pack_index is None:
        context["packs_note"] = ("pack index not found (references/framework-map.md); "
                                 "look the stack up there by hand")
    return context


def format_mapping(mapping: dict, limit: int) -> str:
    items = list(mapping.items())[:limit]
    return ", ".join(f"{key} ({value})" for key, value in items) or "none detected"


def _no_packs(context: dict) -> str:
    return context.get("packs_note") or ("no pack for this stack; use the adaptation questions "
                                         "in references/framework-map.md")


def render_summary(context: dict) -> str:
    lines = [
        "Project context (inferred; confirm before relying on it)",
        "",
        f"  Primary language : {context['primary_language'] or 'unknown'}",
        f"  Languages        : {format_mapping(context['languages'], 6)}",
        f"  Ecosystems       : {', '.join(context['ecosystems']) or 'none detected'}",
        f"  Frameworks       : {', '.join(context['frameworks']) or 'none detected'}",
        f"  Read next        : {', '.join(context['packs']) or _no_packs(context)}",
        f"  Test runners     : {', '.join(context['test_runners']) or 'none detected'}",
        f"  Test files       : {context['tests']['test_file_count']}",
        f"  Source roots     : {', '.join(context['source_roots']) or 'repository root'}",
        f"  Quality tools    : {', '.join(context['quality_tools']) or 'none detected'}",
    ]

    dependencies = context["dependencies"]
    if dependencies:
        versioned = [d for d in dependencies if d["version"]]
        preview = ", ".join(
            f"{d['name']} {d['version']}".strip() for d in dependencies[:5]
        )
        lines.append(
            f"  Dependencies     : {len(dependencies)} declared"
            f" ({len(versioned)} with versions): {preview}..."
        )
        lines.append("    Verify API usage against these versions, not memory;")
        lines.append("    the full list is in context.json.")

    verify = context["suggested_verify_commands"]
    lines.append(f"  Verify with      : {verify[0] if verify else 'unknown; ask the user'}")
    if len(verify) > 1:
        lines.append(f"  Other candidates : {', '.join(verify[1:])}")

    layers = context["layer_candidates"]
    if layers:
        lines.append("")
        lines.append("  Layer candidates (conventional names found in paths):")
        for role, names in layers.items():
            lines.append(f"    {role:<15}{format_mapping(names, 4)}")
        lines.append("    Direction of dependencies is NOT verified here. Declare the")
        lines.append("    intended layering in .clean/architecture.md, then run")
        lines.append("    check_boundaries.py to test whether the code obeys it.")

    context_files = context["existing_context_files"]
    if context_files:
        lines.append("")
        lines.append(f"  Read these first : {', '.join(context_files)}")

    signals = context["purpose"]["signals"]
    if signals:
        lines.append("")
        lines.append("  Signals:")
        lines.extend(f"    - {signal}" for signal in signals)

    return "\n".join(lines)


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect a project's stack, layout, and verification commands.",
    )
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a summary")
    parser.add_argument("--write", action="store_true",
                        help="save the result to <root>/.clean/context.json, merging with an "
                             "existing file (its 'confirmed' object and unknown keys survive)")
    parser.add_argument("--output", default=None,
                        help="write the JSON to this path instead of the default; unlike "
                             "--root-relative defaults, this path resolves from the current "
                             "directory")
    return parser.parse_args(argv)


def merge_with_existing(destination: Path, context: dict) -> dict:
    """Overlay fresh detection onto an existing context file.

    Detector-owned keys are replaced; everything else — the interview's
    "confirmed" object and any keys a future schema may add — survives.
    """
    if not destination.is_file():
        return context
    try:
        existing = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"warning: existing {destination} could not be parsed ({error}); "
              "replacing it", file=sys.stderr)
        return context
    if not isinstance(existing, dict):
        print(f"warning: existing {destination} is not a JSON object; replacing it",
              file=sys.stderr)
        return context
    return {**existing, **context}


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])

    root = Path(arguments.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    context = build_context(root)

    destination = None
    if arguments.write or arguments.output:
        destination = Path(arguments.output) if arguments.output else root / ".clean" / "context.json"
        context = merge_with_existing(destination, context)

    payload = json.dumps(context, indent=2, ensure_ascii=False)

    if arguments.json:
        print(payload)
    else:
        print(render_summary(context))

    if destination is not None:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload + "\n", encoding="utf-8")
        except OSError as error:
            print(f"error: could not write {destination}: {error}", file=sys.stderr)
            return 1
        if not arguments.json:
            print(f"\nSaved: {destination}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
