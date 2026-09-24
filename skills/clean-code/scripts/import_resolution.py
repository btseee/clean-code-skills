#!/usr/bin/env python3
"""Which project files an import names, for drawing the component graph.

Each language finds its dependencies differently: relative paths, dotted
modules, packages and namespaces, module paths from a manifest, include
directories. ModuleIndex learns the project one file at a time during the single
walk, then answers "which files does this import name?" An import it cannot
place -- a third-party package, a standard library module, a generated file -- is
answered with nothing, never a guess.

Some languages reach other files without importing them: Swift shares one
module, Rails autoloads constants, and C#, Java, Kotlin, Scala, and PHP see their
own namespace or package. For those, capitalized names used in code are matched
against the project's declared type names, counting only names declared once.

Standard library only.
"""

from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

import project_files
import project_imports
import source_lexer

_FAMILY_BY_SUFFIX = {
    ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js", ".ts": "js", ".tsx": "js",
    ".mts": "js", ".cts": "js", ".vue": "js", ".svelte": "js",
    ".py": "python", ".pyi": "python",
    ".java": "jvm", ".kt": "jvm", ".kts": "jvm", ".scala": "jvm",
    ".cs": "csharp", ".php": "php", ".go": "go", ".rs": "rust", ".dart": "dart",
    ".rb": "ruby", ".swift": "swift",
    ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".cxx": "c", ".hpp": "c", ".hh": "c",
    ".m": "c", ".mm": "c",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".psm1": "powershell", ".r": "r",
}

_LEXER_BY_FAMILY = {"jvm": "java", "csharp": "csharp", "php": "php", "swift": "swift",
                    "ruby": "ruby"}
TYPE_REFERENCE_FAMILIES = frozenset(_LEXER_BY_FAMILY)
SCOPED_FAMILIES = frozenset({"jvm", "csharp", "php"})
_IMPORT_SUFFIX = {"jvm": ".java", "csharp": ".cs", "php": ".php"}

_JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".vue", ".svelte")
# Under node16/nodenext resolution a relative import names the emitted file, `./order.js`,
# while the project holds `order.ts`.
_TYPESCRIPT_SOURCES = {".js": (".ts", ".tsx"), ".jsx": (".tsx",), ".mjs": (".mts",), ".cjs": (".cts",)}
_TYPE_KINDS = frozenset({"class", "interface", "enum", "struct", "trait", "protocol", "record",
                         "object", "module"})
_CAPITALIZED = re.compile(r"\b[A-Z][A-Za-z0-9_]{2,}\b")
_JVM_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
_CSHARP_NAMESPACE = re.compile(r"^\s*namespace\s+([\w.]+)", re.M)
_PHP_NAMESPACE = re.compile(r"^\s*namespace\s+([\w\\]+)\s*[;{]", re.M)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
_INCLUDE_ROOTS = ("", "include/", "src/", "inc/")


def _family(path: str) -> str:
    return _FAMILY_BY_SUFFIX.get(posixpath.splitext(path)[1].lower(), "")


def _read_jsonc(path: Path):
    """A JSON-with-comments file (tsconfig.json) as data, or None."""
    text = project_files.read_text(path)
    if text is None:
        return None
    text = _TRAILING_COMMA.sub(r"\1", source_lexer.strip(text, "javascript").no_comments)
    try:
        return json.loads(text)
    except ValueError:
        return None


def _first(pattern: re.Pattern, text: str):
    match = pattern.search(text)
    return match.group(1) if match else None


def _visible_namespaces(family: str, namespace: str, path: str, text: str) -> set:
    """Namespaces whose types this file can name without qualifying them.

    C# sees its own namespace and every enclosing one; Java, Kotlin, Scala, and PHP
    see only their own. All of them add what they import, and only that: `using
    Shop.Domain.Orders;` does not make `Shop.Domain` visible, and a single-type import
    is already an edge of its own. A C# using inside the namespace block is relative
    to it: there `using Core;` also names `App.Core` for code in `App.Web`.
    """
    separator = "\\" if family == "php" else "."
    visible = {namespace}
    enclosing = []
    relative_after = None
    if family == "csharp":
        parts = namespace.split(".")
        enclosing = [".".join(parts[:end]) for end in range(1, len(parts) + 1)] if namespace else []
        visible |= set(enclosing)
        declared = _CSHARP_NAMESPACE.search(text)
        relative_after = text.count("\n", 0, declared.start()) + 1 if declared else None
    for line, module in project_imports.imports_in_text(_IMPORT_SUFFIX[family], text):
        module = module.strip(separator).strip("*").rstrip(separator + "._")
        visible.add(module.lower() if family == "php" else module)
        if relative_after is not None and line > relative_after:
            visible |= {f"{outer}.{module}" for outer in enclosing}
    return visible


def _rust_crate_root(source: str) -> str:
    """The nearest enclosing `src` folder: where `crate::` paths start."""
    folders = source.split("/")[:-1]
    for index in range(len(folders) - 1, -1, -1):
        if folders[index] == "src":
            return "/".join(folders[:index + 1])
    return posixpath.dirname(source)


def _strip_script_prefix(module: str) -> str:
    """`"$(dirname "$0")/lib/log.sh"` -> `lib/log.sh`; `$PSScriptRoot\\x.ps1` -> `x.ps1`."""
    module = module.strip("\"'").replace("\\", "/")
    parts = module.split("/")
    while parts and any(marker in parts[0] for marker in ("$", ")", "}", "`")):
        parts = parts[1:]
    return "/".join(parts)


class ModuleIndex:
    """What the project declares, and which of its files an import names."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._files = set()
        self._by_basename = {}
        self._by_directory = {}
        self._python_full = {}
        self._python_suffix = {}
        self._jvm_types = {}
        self._jvm_packages = {}
        self._csharp_namespaces = {}
        self._csharp_types = {}
        self._php_types = {}
        self._php_namespaces = {}
        self._type_owners = {}
        self._declared = {}
        self._references = {}
        self._visible = {}
        self._ts_aliases = []
        self._ts_base = None
        self._go_module = None
        self._dart_package = None
        self._read_manifests()

    # --- learning the project -------------------------------------------------------

    def _read_manifests(self) -> None:
        for name in ("tsconfig.json", "jsconfig.json"):
            config = _read_jsonc(self.root / name)
            if isinstance(config, dict):
                options = config.get("compilerOptions") or {}
                base = options.get("baseUrl")
                base_dir = posixpath.normpath(base) if isinstance(base, str) else "."
                if isinstance(base, str):
                    self._ts_base = base_dir
                for pattern, targets in (options.get("paths") or {}).items():
                    if isinstance(targets, list):
                        self._ts_aliases.append((pattern, [
                            posixpath.normpath(posixpath.join(base_dir, target))
                            for target in targets if isinstance(target, str)
                        ]))
                break
        go_mod = project_files.read_text(self.root / "go.mod") or ""
        self._go_module = _first(re.compile(r"^module\s+(\S+)", re.M), go_mod)
        pubspec = project_files.read_text(self.root / "pubspec.yaml") or ""
        self._dart_package = _first(re.compile(r"^name:\s*(\S+)", re.M), pubspec)

    def add(self, path: str, text: str, symbols) -> None:
        """Learn one file: its path, what it declares, and the names its code uses."""
        self._files.add(path)
        self._by_basename.setdefault(posixpath.basename(path), set()).add(path)
        family = _family(path)
        if family in {"go"} and not path.endswith("_test.go"):
            self._by_directory.setdefault(posixpath.dirname(path), set()).add(path)
        if family == "python":
            self._add_python(path)
        top_types = [symbol.name for symbol in (symbols.symbols if symbols else [])
                     if symbol.parent is None and symbol.kind in _TYPE_KINDS]
        namespace = None
        if family == "jvm":
            namespace = _first(_JVM_PACKAGE, text) or ""
            self._jvm_packages.setdefault(namespace, set()).add(path)
            for name in top_types:
                self._jvm_types[f"{namespace}.{name}" if namespace else name] = path
        elif family == "csharp":
            namespaces = _CSHARP_NAMESPACE.findall(text)
            namespace = namespaces[0] if namespaces else ""
            for declared in namespaces:
                self._csharp_namespaces.setdefault(declared, set()).add(path)
            for name in top_types:
                self._csharp_types[f"{namespace}.{name}" if namespace else name] = path
        elif family == "php":
            namespace = (_first(_PHP_NAMESPACE, text) or "").strip("\\").lower()
            self._php_namespaces.setdefault(namespace, set()).add(path)
            for name in top_types:
                self._php_types[f"{namespace}\\{name.lower()}".strip("\\")] = path
        if family in TYPE_REFERENCE_FAMILIES:
            self._declared[path] = set(top_types)
            for name in top_types:
                self._type_owners.setdefault((family, name), set()).add((path, namespace))
            if family in SCOPED_FAMILIES:
                self._visible[path] = _visible_namespaces(family, namespace, path, text)
            code = source_lexer.strip(text, _LEXER_BY_FAMILY[family]).code
            self._references[path] = set(_CAPITALIZED.findall(code))

    def _add_python(self, path: str) -> None:
        parts = posixpath.splitext(path)[0].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            return
        self._python_full[".".join(parts)] = path
        for start in range(1, len(parts) - 1):
            self._python_suffix.setdefault(".".join(parts[start:]), set()).add(path)
        if len(parts) == 1 or (len(parts) == 2 and parts[0] in {"src", "lib"}):
            self._python_suffix.setdefault(parts[-1], set()).add(path)

    # --- answering -------------------------------------------------------------------

    def resolve(self, source_path: str, module: str) -> list:
        """Project files the import `module` in `source_path` names; [] when none."""
        resolver = {
            "js": self._resolve_js, "python": self._resolve_python, "jvm": self._resolve_jvm,
            "csharp": self._resolve_csharp, "php": self._resolve_php, "go": self._resolve_go,
            "rust": self._resolve_rust, "dart": self._resolve_dart, "ruby": self._resolve_ruby,
            "c": self._resolve_include, "shell": self._resolve_script,
            "powershell": self._resolve_script, "r": self._resolve_r,
        }.get(_family(source_path))
        if resolver is None or not module:
            return []
        return sorted(set(resolver(source_path, module.strip())))

    def resolve_type_references(self, source_path: str) -> list:
        """Files declaring the capitalized names this file's code uses, where unique.

        In C#, the JVM languages, and PHP a name is only visible from the file's own
        namespace or package and the ones it imports; elsewhere a type name is global.
        """
        family = _family(source_path)
        names = self._references.get(source_path, set()) - self._declared.get(source_path, set())
        visible = self._visible.get(source_path)
        found = set()
        for name in names:
            owners = {path for path, namespace in self._type_owners.get((family, name), set())
                      if visible is None or namespace in visible}
            if len(owners) == 1 and source_path not in owners:
                found |= owners
        return sorted(found)

    def _existing(self, candidates) -> list:
        for candidate in candidates:
            normalized = posixpath.normpath(candidate)
            if not normalized.startswith("..") and normalized in self._files:
                return [normalized]
        return []

    def _js_candidates(self, base: str) -> list:
        stem, suffix = posixpath.splitext(base)
        sources = [stem + source for source in _TYPESCRIPT_SOURCES.get(suffix, ())]
        return self._existing([base] + sources + [base + extension for extension in _JS_EXTENSIONS] +
                              [f"{base}/index{extension}" for extension in _JS_EXTENSIONS])

    def _resolve_js(self, source: str, module: str) -> list:
        if module.startswith("."):
            return self._js_candidates(posixpath.join(posixpath.dirname(source), module))
        for pattern, targets in self._ts_aliases:
            if pattern.endswith("*") and module.startswith(pattern[:-1]):
                rest = module[len(pattern) - 1:]
                for target in targets:
                    found = self._js_candidates(target.replace("*", rest))
                    if found:
                        return found
            elif module == pattern:
                for target in targets:
                    found = self._js_candidates(target)
                    if found:
                        return found
        if self._ts_base is not None:
            return self._js_candidates(posixpath.join(self._ts_base, module))
        return []

    def _resolve_python(self, source: str, module: str) -> list:
        if module.startswith("."):
            dots = len(module) - len(module.lstrip("."))
            base = posixpath.dirname(source)
            for _ in range(dots - 1):
                base = posixpath.dirname(base)
            rest = module[dots:].replace(".", "/")
            target = posixpath.join(base, rest) if rest else base
            return self._existing([target + ".py", target + ".pyi", target + "/__init__.py"])
        parts = module.split(".")
        for end in range(len(parts), 0, -1):
            key = ".".join(parts[:end])
            if key in self._python_full:
                return [self._python_full[key]]
            owners = self._python_suffix.get(key, set())
            if len(owners) == 1:
                return list(owners)
            if owners:
                return []
        return []

    def _resolve_jvm(self, source: str, module: str) -> list:
        module = module.replace(" ", "")
        grouped = re.match(r"^([\w.]+)\.\{([^}]*)\}$", module)
        if grouped:
            found = []
            for name in grouped.group(2).split(","):
                found += self._resolve_jvm(source, f"{grouped.group(1)}.{name.split('=>')[0]}")
            return found
        if module.endswith((".*", "._")):
            return list(self._jvm_packages.get(module[:-2], ()))
        parts = module.split(".")
        for end in range(len(parts), 0, -1):
            key = ".".join(parts[:end])
            if key in self._jvm_types:
                return [self._jvm_types[key]]
        for end in range(len(parts), 0, -1):
            key = ".".join(parts[:end])
            if key in self._jvm_packages and key:
                return list(self._jvm_packages[key])
        return []

    def _resolve_csharp(self, source: str, module: str) -> list:
        if module in self._csharp_namespaces:
            return list(self._csharp_namespaces[module])
        if module in self._csharp_types:
            return [self._csharp_types[module]]
        parent = module.rsplit(".", 1)[0]
        return list(self._csharp_namespaces.get(parent, ())) if "." in module else []

    def _resolve_php(self, source: str, module: str) -> list:
        key = module.strip("\\").lower()
        if key in self._php_types:
            return [self._php_types[key]]
        return list(self._php_namespaces.get(key, ()))

    def _resolve_go(self, source: str, module: str) -> list:
        if not self._go_module:
            return []
        if module == self._go_module:
            return list(self._by_directory.get("", ()))
        prefix = self._go_module + "/"
        if not module.startswith(prefix):
            return []
        return list(self._by_directory.get(module[len(prefix):], ()))

    def _resolve_rust(self, source: str, module: str) -> list:
        segments = [segment for segment in module.strip(":").split("::") if segment]
        if not segments:
            return []
        stem = posixpath.splitext(posixpath.basename(source))[0]
        here = posixpath.dirname(source) if stem in {"lib", "main", "mod"} else \
            posixpath.join(posixpath.dirname(source), stem)
        head = segments[0]
        if head == "crate":
            base, rest = _rust_crate_root(source), segments[1:]
        elif head == "self":
            base, rest = here, segments[1:]
        elif head == "super":
            base, rest = here, segments
            while rest and rest[0] == "super":
                base, rest = posixpath.dirname(base), rest[1:]
        else:
            base, rest = here, segments
        for end in range(len(rest), 0, -1):
            candidate = posixpath.join(base, *rest[:end])
            found = self._existing([candidate + ".rs", candidate + "/mod.rs"])
            if found:
                return found
        return []

    def _resolve_dart(self, source: str, module: str) -> list:
        if module.startswith("dart:"):
            return []
        if module.startswith("package:"):
            package, _, rest = module[len("package:"):].partition("/")
            if package != self._dart_package:
                return []
            return self._existing(["lib/" + rest])
        return self._existing([posixpath.join(posixpath.dirname(source), module)])

    def _resolve_ruby(self, source: str, module: str) -> list:
        name = module if module.endswith(".rb") else module + ".rb"
        return self._existing([posixpath.join(posixpath.dirname(source), name),
                               "lib/" + name, name])

    def _resolve_include(self, source: str, module: str) -> list:
        if module.startswith("<"):
            # A system include names a project file only by its path under an include root.
            return self._existing([root + module[1:] for root in _INCLUDE_ROOTS])
        found = self._existing([posixpath.join(posixpath.dirname(source), module)] +
                               [root + module for root in _INCLUDE_ROOTS])
        if found:
            return found
        owners = self._by_basename.get(posixpath.basename(module), set())
        return list(owners) if len(owners) == 1 else []

    def _resolve_script(self, source: str, module: str) -> list:
        relative = _strip_script_prefix(module)
        if not relative:
            return []
        return self._existing([posixpath.join(posixpath.dirname(source), relative), relative])

    def _resolve_r(self, source: str, module: str) -> list:
        return self._existing([module, posixpath.join(posixpath.dirname(source), module)])
