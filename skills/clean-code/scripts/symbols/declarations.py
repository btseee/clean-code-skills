#!/usr/bin/env python3
"""The variables and parameters a source file declares, where they read reliably.

Python's come from the tree python_source already parsed; JavaScript's and TypeScript's from
`const`, `let`, `var`, and the parameter lists of named functions on the lexer's code view. A
name that a loop, a catch, a lambda, or another author dictates is left out: only names the
file's author chose are declarations here.

Standard library only.
"""

from __future__ import annotations

import ast
import bisect
import re
from typing import Optional

from source import lexer as source_lexer

from .model import Declaration

SCRIPT_LANGUAGES = frozenset({"javascript", "typescript"})


def _by_line(declarations) -> tuple:
    """Declarations in line order, a line's parameters before its variables."""
    return tuple(sorted(declarations, key=lambda declaration: (declaration.line,
                                                               declaration.kind != "parameter")))


# --- Python ---------------------------------------------------------------------------------------


def _parameters(arguments) -> list:
    """Every parameter of a signature, positional-only to `**kwargs`."""
    listed = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    return listed + [parameter for parameter in (arguments.vararg, arguments.kwarg) if parameter]


def _assigned_targets(statement) -> list:
    if isinstance(statement, ast.Assign):
        return statement.targets
    if isinstance(statement, ast.AnnAssign):
        return [statement.target]
    return []


def _nested_statements(statement) -> list:
    """The statements inside a compound statement: its bodies, and each handler's or case's."""
    nested = []
    for field in ("body", "orelse", "finalbody"):
        nested += getattr(statement, field, None) or []
    clauses = (getattr(statement, "handlers", None) or []) + (getattr(statement, "cases", None) or [])
    for clause in clauses:
        nested += clause.body
    return nested


def _bound_names(target) -> list:
    """The plain names a target binds: `a` and `b` in `a, (b, *rest) = ...`, never `self.a`."""
    if isinstance(target, ast.Name):
        return [target]
    if isinstance(target, ast.Starred):
        return _bound_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for element in target.elts for name in _bound_names(element)]
    return []


def _bind(first_bindings: dict, scope, declaration: Declaration) -> None:
    """Record a binding in scope unless an earlier line bound the name: rebinding a parameter or
    a variable declares nothing new."""
    key = (scope, declaration.name)
    if key not in first_bindings or declaration.line < first_bindings[key].line:
        first_bindings[key] = declaration


def python_declarations(tree) -> tuple:
    """Parameters and assigned variables, each at its first binding in its scope.

    Only statements are walked: loop and `with` targets, `except` names, comprehension targets,
    and lambda parameters are short-lived, a walrus target lives inside an expression, and class
    attributes are fields, so none are declarations. A stack, not recursion, keeps deep nesting
    safe.
    """
    first_bindings = {}
    # Each entry: a statement, the scope its names bind in, and whether it sits in a class body.
    pending = [(statement, tree, False) for statement in tree.body]
    while pending:
        statement, scope, in_class = pending.pop()
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = scope.name if in_class else None
            for parameter in _parameters(statement.args):
                _bind(first_bindings, statement,
                      Declaration(parameter.arg, "parameter", parameter.lineno, owner))
            pending += [(nested, statement, False) for nested in statement.body]
        elif isinstance(statement, ast.ClassDef):
            pending += [(nested, statement, True) for nested in statement.body]
        else:
            if not in_class:
                for target in _assigned_targets(statement):
                    for name in _bound_names(target):
                        _bind(first_bindings, scope, Declaration(name.id, "variable", name.lineno))
            pending += [(nested, scope, in_class) for nested in _nested_statements(statement)]
    return _by_line(first_bindings.values())


# --- JavaScript and TypeScript ----------------------------------------------------------------

_DECLARATION = re.compile(r"(?<![\w$.])(?:const|let|var)\b")
_FOR_HEADER = re.compile(r"\bfor\s*(?:await\s*)?\(\s*$")
_SCRIPT_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
_PROPERTY_KEY = re.compile(r"[A-Za-z_$][\w$]*|\d+|\"[^\"\n]*\"|'[^'\n]*'")
_REQUIRE_CALL = re.compile(r"\s*require\s*\(")
_SPACE = re.compile(r"\s*")
_FUNCTION_KEYWORD = re.compile(r"(?<![\w$.])function\b(?:\s*\*)?\s*(?:(?P<name>[A-Za-z_$][\w$]*)\s*)?"
                               r"(?:<[^<>()]*>\s*)?\(")
_METHOD = re.compile(r"^[ \t]*(?:(?:public|private|protected|static|async|readonly|override|abstract|"
                     r"get|set|accessor)[ \t]+)*(?:\*[ \t]*)?(?P<name>#?[A-Za-z_$][\w$]*)[ \t]*"
                     r"(?:<[^<>\n]*>[ \t]*)?\(", re.M)
_METHOD_BODY = re.compile(r"\s*(?::[^{};=]*)?\{")
_NOT_METHODS = frozenset({"if", "for", "while", "switch", "catch", "function", "return", "with",
                          "typeof", "new", "delete", "void", "await", "yield", "super", "import",
                          "export", "else", "do", "try", "throw", "case", "default", "in", "of",
                          "instanceof"})
_ARROW = re.compile(r"=>")
_RETURN_TYPE = re.compile(r"\)\s*:[^=;{}()]*$")
_ASSIGNED = re.compile(r"=\s*(?:async\s+)?(?:<[^<>()]*>\s*)?$")
_TYPE_ALIAS = re.compile(r"\btype\s+[A-Za-z_$][\w$]*\s*(?:<[^<>]*>\s*)?=\s*(?:<[^<>()]*>\s*)?$")
_PARAMETER_MODIFIER = re.compile(r"(?:public|private|protected|readonly|override)\s+")
_DECORATOR = re.compile(r"@[\w$.]+")
_DECLARATOR_TOKENS = re.compile(r"[()\[\]{},;<>\n]")
_ELEMENT_TOKENS = re.compile(r"[()\[\]{},]")
_PARAMETER_TOKENS = re.compile(r"=>|[()\[\]{}<>,]")
_ANNOTATION_TOKENS = re.compile(r"=>|[()\[\]{}<>=,;\n]")
# How far back the assignment naming a function, or an arrow's return type, may start.
_LOOKBEHIND = 200
_MAX_PARAMETER_SPAN = 1000
_MAX_PATTERN_NESTING = 8


def _skip_space(code: str, index: int) -> int:
    return _SPACE.match(code, index).end()


def _skip_space_back(code: str, index: int) -> int:
    while index >= 0 and code[index] in " \t\r\n":
        index -= 1
    return index


def _element_end(code: str, index: int) -> int:
    """The offset of the `,` or closing bracket ending the element at index; a default value
    (`= []`) is passed over."""
    depth = 0
    for token in _ELEMENT_TOKENS.finditer(code, index):
        if token.group() in "([{":
            depth += 1
        elif depth == 0:
            return token.start()
        elif token.group() != ",":
            depth -= 1
    return len(code)


def _property_key_end(code: str, index: int) -> int:
    """The offset after the property key at index: a name, a string, a number, or `[computed]`."""
    key = _PROPERTY_KEY.match(code, index)
    if key:
        return key.end()
    if code.startswith("[", index):
        return _element_end(code, index + 1) + 1
    return index


def _binding(code: str, index: int, nesting: int = 0) -> tuple:
    """([(name, offset)], end) for the identifier or destructuring pattern at index.

    A shorthand property (`{ data }`) takes the object's key as its name, chosen by the object's
    author, so it binds no name here; a renamed one (`{ data: rows }`) does.
    """
    index = _skip_space(code, index)
    identifier = _SCRIPT_IDENTIFIER.match(code, index)
    if identifier:
        return [(identifier.group(), index)], identifier.end()
    if nesting > _MAX_PATTERN_NESTING or not code.startswith(("{", "["), index):
        return [], index
    closer = "}" if code[index] == "{" else "]"
    names = []
    index += 1
    while True:
        index = _skip_space(code, index)
        if index >= len(code) or code[index] == closer:
            return names, index + 1
        if code[index] == ",":         # a hole in an array pattern
            index += 1
            continue
        if code.startswith("...", index):
            found, index = _binding(code, index + 3, nesting + 1)
            names += found
        elif closer == "]":
            found, index = _binding(code, index, nesting + 1)
            names += found
        else:
            index = _skip_space(code, _property_key_end(code, index))
            if code.startswith(":", index):
                found, index = _binding(code, index + 1, nesting + 1)
                names += found
        index = _element_end(code, index)
        if index >= len(code) or code[index] not in (",", closer):
            return names, index        # not a pattern after all
        if code[index] == ",":
            index += 1


def _skip_annotation(code: str, index: int) -> int:
    """The offset after a TypeScript `: Type` annotation at index, if there is one."""
    index = _skip_space(code, index)
    if not code.startswith(":", index):
        return index
    depth = 0
    for token in _ANNOTATION_TOKENS.finditer(code, index + 1):
        character = token.group()
        if character == "=>":
            continue
        if character in "([{<":
            depth += 1
        elif character in ")]}>":
            if depth == 0:
                return token.start()
            depth -= 1
        elif depth == 0:
            return token.start()        # `=`, `,`, `;`, or a line break
    return len(code)


def _declarator_end(code: str, index: int) -> tuple:
    """(offset, whether another declarator follows) for the end of the declarator at index.
    Reading stops at a line break, and at `<` or `>`, which may open JSX or generics."""
    depth = 0
    for token in _DECLARATOR_TOKENS.finditer(code, index):
        character = token.group()
        if character in "([{":
            depth += 1
        elif character in ")]}":
            if depth == 0:
                return token.start(), False
            depth -= 1
        elif depth == 0:
            return token.start(), character == ","
    return len(code), False


def _declared_variables(code: str, declaration) -> list:
    """(name, offset) for each name one `const`, `let`, or `var` declares. A for loop's variable
    is short-lived, and a `require`d module's alias mirrors the module's name: neither counts."""
    start = declaration.start()
    if _FOR_HEADER.search(code, max(0, start - 30), start):
        return []
    index = _skip_space(code, declaration.end())
    names = []
    while True:
        index = _skip_space(code, index)
        is_pattern = code.startswith(("{", "["), index)
        begin = index
        bindings, index = _binding(code, index)
        if index == begin:
            return names
        index = _skip_annotation(code, index)
        initialized = code.startswith("=", index) and not code.startswith("=>", index)
        if is_pattern or not (initialized and _REQUIRE_CALL.match(code, index + 1)):
            names += bindings
        index, more = _declarator_end(code, index)
        if not more:
            return names
        index += 1


def _is_assigned_a_name(code: str, head: int) -> bool:
    """Whether the function whose `function` keyword or parameters start at head is assigned a
    name: `const total = (...) =>`, or a class field. An arrow typed in an alias
    (`type Total = (x) => number`) is no function."""
    window = max(0, head - _LOOKBEHIND)
    return bool(_ASSIGNED.search(code, window, head)) and not _TYPE_ALIAS.search(code, window, head)


def _opening_paren(code: str, close: int) -> Optional[int]:
    depth = 0
    for index in range(close, max(-1, close - _MAX_PARAMETER_SPAN), -1):
        if code[index] == ")":
            depth += 1
        elif code[index] == "(":
            depth -= 1
            if depth == 0:
                return index
    return None


def _arrow_parameters_start(code: str, arrow: int) -> Optional[int]:
    """Where the parameters of the arrow function at arrow start: its `(`, or its lone parameter."""
    end = _skip_space_back(code, arrow - 1)
    if end < 0:
        return None
    if code[end] != ")":
        annotated = _RETURN_TYPE.search(code, max(0, arrow - _LOOKBEHIND), arrow)
        if annotated is not None:
            end = annotated.start()
    if code[end] == ")":
        return _opening_paren(code, end)
    start = end
    while start > 0 and (code[start - 1].isalnum() or code[start - 1] in "_$"):
        start -= 1
    before = _skip_space_back(code, start - 1)
    if not _SCRIPT_IDENTIFIER.fullmatch(code, start, end + 1) or (before >= 0 and code[before] in ":."):
        return None         # a return type, or a member
    return start


def _parameter_list_starts(code: str) -> set:
    """Offsets where the parameters of each function with a chosen name start: a function
    declaration, a method, or a function or arrow assigned to a name. A function passed as an
    argument is a lambda, its parameters short-lived."""
    starts = set()
    for match in _FUNCTION_KEYWORD.finditer(code):
        if match.group("name") or _is_assigned_a_name(code, match.start()):
            starts.add(match.end() - 1)
    for match in _METHOD.finditer(code):
        close = source_lexer.closing_paren(code, match.end() - 1)
        if match.group("name") not in _NOT_METHODS and close >= 0 and _METHOD_BODY.match(code, close + 1):
            starts.add(match.end() - 1)
    for match in _ARROW.finditer(code):
        start = _arrow_parameters_start(code, match.start())
        if start is not None and _is_assigned_a_name(code, start):
            starts.add(start)
    return starts


def _parameter_start(code: str, index: int, close: int) -> int:
    """The offset of the binding a parameter declares, past decorators, modifiers, and `...`."""
    while index < close:
        index = _skip_space(code, index)
        decorator = _DECORATOR.match(code, index)
        modifier = _PARAMETER_MODIFIER.match(code, index)
        if decorator:
            index = _skip_space(code, decorator.end())
            if code.startswith("(", index):
                end = source_lexer.closing_paren(code, index)
                index = end + 1 if end >= 0 else close
        elif modifier:
            index = modifier.end()
        elif code.startswith("...", index):
            index += 3
        else:
            return index
    return index


def _parameter_end(code: str, index: int, close: int) -> int:
    """The offset of the `,` ending the parameter at index, or close."""
    depth = 0
    for token in _PARAMETER_TOKENS.finditer(code, index, close):
        character = token.group()
        if character == "=>":
            continue
        if character in "([{<":
            depth += 1
        elif character in ")]}>":
            depth = max(depth - 1, 0)
        elif depth == 0:
            return token.start()
    return close


def _parameter_names(code: str, start: int) -> list:
    """(name, offset) for each parameter the list at start declares: a `(` list, or an arrow's
    lone parameter."""
    if code[start] != "(":
        identifier = _SCRIPT_IDENTIFIER.match(code, start)
        return [(identifier.group(), start)] if identifier else []
    close = source_lexer.closing_paren(code, start)
    names = []
    index = start + 1
    while 0 <= index < close:
        index = _parameter_start(code, index, close)
        bindings, index = _binding(code, index)
        names += [(name, offset) for name, offset in bindings if offset < close]
        index = _parameter_end(code, index, close) + 1
    return names


def script_declarations(text: str, language: str) -> tuple:
    """Variables from `const`, `let`, and `var`, and the parameters of named functions."""
    code = source_lexer.strip(text, language).code
    line_starts = [0] + [match.end() for match in re.finditer("\n", code)]

    def declared_at(name: str, offset: int, kind: str) -> Declaration:
        return Declaration(name, kind, bisect.bisect_right(line_starts, offset))

    names = [declared_at(name, offset, "variable") for declaration in _DECLARATION.finditer(code)
             for name, offset in _declared_variables(code, declaration)]
    names += [declared_at(name, offset, "parameter") for start in sorted(_parameter_list_starts(code))
              for name, offset in _parameter_names(code, start)]
    return _by_line(names)
