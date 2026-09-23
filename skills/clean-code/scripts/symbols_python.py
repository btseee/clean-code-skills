#!/usr/bin/env python3
"""Symbols declared in a Python file, read with the standard library's own parser.

Standard library only.
"""

from __future__ import annotations

import ast
from typing import Optional

import source_lexer
import symbol_model
from symbol_model import Symbol

_ABSTRACT_BASES = {"ABC", "ABCMeta"}
_PROTOCOL_BASES = {"Protocol"}


def _name_of(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _name_of(node.value)
    return ""


def _declared_all(tree) -> Optional[set]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                return {
                    element.value for element in node.value.elts
                    if isinstance(element, ast.Constant) and isinstance(element.value, str)
                }
    return None


def _is_abstract_method(node) -> bool:
    return any(_name_of(decorator) == "abstractmethod" for decorator in node.decorator_list)


def _class_kind(node) -> tuple:
    """(kind, abstract) for a class definition."""
    bases = {_name_of(base) for base in node.bases}
    if bases & _PROTOCOL_BASES:
        return "protocol", True
    metaclass = {_name_of(keyword.value) for keyword in node.keywords if keyword.arg == "metaclass"}
    methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    abstract = bool(bases & _ABSTRACT_BASES or metaclass & _ABSTRACT_BASES
                    or any(_is_abstract_method(method) for method in methods))
    return "class", abstract


class _Builder:
    def __init__(self, path: str, text: str):
        self.path = path
        self.raw_lines = text.split("\n")
        self.nc_lines = source_lexer.strip(text, "python").no_comments.split("\n")

    def context(self, node) -> str:
        first = min([node.lineno] + [decorator.lineno for decorator in node.decorator_list])
        lines = []
        for number in range(first, min(node.lineno + 3, len(self.raw_lines)) + 1):
            line = self.raw_lines[number - 1].rstrip()
            lines.append(line)
            if number >= node.lineno and line.rstrip().endswith(":"):
                break
        return "\n".join(lines)

    def fingerprints(self, node) -> tuple:
        body = self.nc_lines[node.lineno:getattr(node, "end_lineno", node.lineno)]
        return symbol_model.fingerprints(body)

    def symbol(self, node, kind: str, exported: bool, parent=None, abstract=False) -> Symbol:
        exact, shape = (None, None)
        if kind in {"function", "method"}:
            exact, shape = self.fingerprints(node)
        return Symbol(
            name=node.name,
            kind=kind,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            exported=exported,
            parent=parent,
            doc=symbol_model.first_sentence(ast.get_docstring(node) or ""),
            context=self.context(node),
            exact=exact,
            shape=shape,
            abstract=abstract,
        )


def extract(path: str, text: str) -> symbol_model.FileSymbols:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return symbol_model.file_symbols(path, "python", "", text, [])

    builder = _Builder(path, text)
    declared = _declared_all(tree)

    def exported(name: str) -> bool:
        return name in declared if declared is not None else not name.startswith("_")

    symbols = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            kind, abstract = _class_kind(node)
            symbols.append(builder.symbol(node, kind, exported(node.name), abstract=abstract))
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(builder.symbol(
                        item, "method", not item.name.startswith("_"), parent=node.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(builder.symbol(node, "function", exported(node.name)))

    purpose = symbol_model.first_sentence(ast.get_docstring(tree) or "")
    return symbol_model.file_symbols(path, "python", purpose, text, symbols)
