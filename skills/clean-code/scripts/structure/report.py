#!/usr/bin/env python3
"""The structure map as people and agents read it: .clean/structure.md and a summary.

structure.md is ordered so that a partial read still gets the most important part
first: the findings, the moves they propose, then the folder tree, then the
components, then one greppable row per file. A model with a small context window
reads the top and greps the Files table for the paths it is about to change.

Standard library only.
"""

from __future__ import annotations

import posixpath
from collections import Counter, defaultdict

ORGANIZATION_TITLES = (
    ("family", "Families"),
    ("junk_drawer", "Junk drawers"),
    ("flat_folder", "Flat folders"),
    ("unreferenced", "Unreferenced"),
    ("comment_heavy", "Comment-heavy"),
)
FINDING_TITLES = (
    ("misplaced", "Misplaced"),
    ("mixed", "Mixed"),
    ("duplicates", "Duplicates"),
    ("name_clashes", "Name clashes"),
    ("synonyms", "Synonyms"),
) + ORGANIZATION_TITLES + (
    ("names", "Names"),
    ("cycles", "Cycles"),
)
# The terminal summary keeps the order it had before names and the organization findings were
# reported, then adds them, so a reader comparing runs sees the same line with more counts.
SUMMARY_TITLES = (tuple((key, title) for key, title in FINDING_TITLES
                        if key != "names" and (key, title) not in ORGANIZATION_TITLES)
                  + (("names", "Names"),) + ORGANIZATION_TITLES)
FOLDER_FINDINGS = frozenset({"family", "junk_drawer", "flat_folder"})
NAME_EXAMPLES = 5
MAX_TREE_ROWS = 200
MAX_GRAPH_NODES = 25
MAX_SYMBOLS_PER_ROW = 8
MAX_UNPARSED_SHOWN = 10
SUMMARY_PER_KIND = 5


def _cell(text) -> str:
    """Text safe inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _code(text) -> str:
    return "`" + str(text).replace("`", "'") + "`"


def _where(finding) -> str:
    return f"{finding['path']}:{finding['line']}"


def _destination(suggestion) -> str:
    """Where a finding sends code: a folder, a file, or its own file named like a pattern."""
    if not suggestion:
        return "its role's home"
    folder, _, name = suggestion.rpartition("/")
    if " " not in suggestion and any(mark in name for mark in "*?"):
        return f"its own file named like {_code(name)}" + (f" in {_code(folder + '/')}" if folder else "")
    return _code(suggestion)


def _misplaced_line(finding) -> str:
    target = _destination(finding["suggestion"])
    if finding["symbol"] is None:
        return f"{_code(finding['path'])} holds only {finding['role']} code; move the file to {target}."
    home = f"a {finding['home_role']} file" if finding["home_role"] else "this file"
    return (f"{_code(_where(finding))} {_code(finding['symbol'])} is {finding['role']} in {home}; "
            f"move it to {target}.")


def _mixed_line(finding) -> str:
    parts = [f"{role} ({', '.join(_code(name) for name in names[:3])})"
             for role, names in finding["roles"].items()]
    return f"{_code(finding['path'])} mixes {', '.join(parts)}."


def _duplicate_line(finding) -> str:
    members = ", ".join(f"{_code(_where(member))} {_code(member['symbol'])}"
                        for member in finding["members"][:6])
    more = f", and {len(finding['members']) - 6} more" if len(finding["members"]) > 6 else ""
    return f"{finding['kind']}, {finding['lines']} lines: {members}{more}"


def _clash_line(finding) -> str:
    members = ", ".join(_code(_where(member)) for member in finding["members"][:6])
    return f"{_code(finding['name'])} ({finding['language']}): {members}"


def _synonym_line(finding) -> str:
    verbs = ", ".join(f"{verb} x{len(entries)} ({_code(_where(entries[0]))})"
                      for verb, entries in finding["verbs"].items())
    return f"{finding['noun']} ({finding['group']}): {verbs}"


def _cycle_line(finding) -> str:
    names = finding["components"]
    shown = " <-> ".join(_code(name) for name in names[:8])
    if len(names) > 8:
        shown += f" and {len(names) - 8} more"
    heaviest = sorted(finding["edges"], key=lambda edge: -edge["count"])[:6]
    counts = ", ".join(f"{edge['from']} -> {edge['to']} x{edge['count']}" for edge in heaviest)
    more = f", {len(finding['edges']) - 6} more edges" if len(finding["edges"]) > 6 else ""
    return f"{shown} ({counts}{more})"


def _folder(folder: str) -> str:
    return _code(folder + "/" if folder else "./")


def _file_names(paths, shown: int) -> str:
    names = ", ".join(_code(posixpath.basename(path)) for path in paths[:shown])
    return names + (f", and {len(paths) - shown} more" if len(paths) > shown else "")


def _family_line(family) -> str:
    return (f"{_file_names(family['files'], 6)} in {_folder(family['folder'])} share "
            f"{_code(family['token'])} and import each other; group them in {_code(family['suggestion'])}.")


def _junk_drawer_split(split) -> str:
    files = _file_names(split["files"], 3)
    if split["by"] == "unsorted":
        return f"{files}: give each file a named home"
    if split["by"] == "name":
        return f"{_code(split['name'])} ({files}) share a name"
    label = split["name"] if split["by"] == "role" else f"{split['name']} family"
    return f"{label} ({files}) -> {_destination(split['to'])}"


def _junk_drawer_line(drawer) -> str:
    if drawer["rename"]:
        return f"{_folder(drawer['folder'])} holds one concept; rename it {_code(drawer['rename'])}."
    splits = "; ".join(_junk_drawer_split(split) for split in drawer["splits"])
    return f"{_folder(drawer['folder'])} is named for no concept; split it: {splits}."


def _flat_folder_line(crowded) -> str:
    families = ", ".join(_code(token) for token in crowded["families"])
    start = f", starting with its families {families}" if families else ""
    return (f"{_folder(crowded['folder'])} holds {crowded['file_count']} source files; "
            f"group them by concept{start}.")


def _unreferenced_line(unused) -> str:
    return f"{_code(unused['path'])} is possibly unused: no file imports it."


def _comment_heavy_line(commented) -> str:
    return (f"{_code(commented['path'])}: {commented['comment_lines']} of {commented['nonblank_lines']} "
            f"lines are comments ({round(100 * commented['ratio'])}%).")


LINE_RENDERERS = {
    "misplaced": _misplaced_line, "mixed": _mixed_line, "duplicates": _duplicate_line,
    "name_clashes": _clash_line, "synonyms": _synonym_line, "cycles": _cycle_line,
    "family": _family_line, "junk_drawer": _junk_drawer_line, "flat_folder": _flat_folder_line,
    "unreferenced": _unreferenced_line, "comment_heavy": _comment_heavy_line,
}


def _name_rule_lines(items, examples: int) -> tuple:
    """(lines, unlisted): one line per naming rule, the most frequent first, with its count and
    first examples; and how many findings no line lists."""
    by_rule = defaultdict(list)
    for item in items:
        by_rule[item["rule"]].append(item)
    lines = []
    for rule, found in sorted(by_rule.items(), key=lambda entry: (-len(entry[1]), entry[0])):
        shown = ", ".join(f"{_code(item['name'])} ({_code(_where(item))})" for item in found[:examples])
        more = ", ..." if len(found) > examples else ""
        listed = f" — {shown}{more}" if shown else ""
        lines.append(f"{rule} ({found[0]['cites']}): {len(found)}{listed}")
    unlisted = sum(max(0, len(found) - examples) for found in by_rule.values())
    return lines, unlisted


def _flagged(structure_map) -> dict:
    """path -> finding kinds that name the file, and the misplaced symbol names."""
    kinds = defaultdict(set)
    symbols = defaultdict(set)
    findings = structure_map["findings"]
    for item in findings["misplaced"]:
        kinds[item["path"]].add("misplaced")
        if item["symbol"]:
            symbols[item["path"]].add(item["symbol"])
    for item in findings["mixed"]:
        kinds[item["path"]].add("mixed")
    for group in findings["duplicates"]:
        for member in group["members"]:
            kinds[member["path"]].add("duplicates")
    for group in findings["name_clashes"]:
        for member in group["members"]:
            kinds[member["path"]].add("name_clashes")
    return {"kinds": kinds, "symbols": symbols}


def _header(structure_map) -> list:
    commit = f" at commit {_code(structure_map['commit'])}" if structure_map.get("commit") else ""
    languages = ", ".join(f"{name} {count}" for name, count in structure_map["languages"].items()) or "none"
    packs = ", ".join(_code(pack) for pack in structure_map["packs"]) or "none (generic conventions only)"
    lines = [
        "# Structure Map",
        "",
        f"Generated by `map_structure.py` on {structure_map['generated']}{commit}. Evidence for judgement, "
        "not a verdict: read each finding, then decide. Regenerate when the commit differs from "
        "`git rev-parse --short HEAD`.",
        "",
        f"- Files: {structure_map['file_count']} source, {structure_map['test_file_count']} test; "
        f"{structure_map['symbol_count']} top-level symbols; {languages}",
        f"- Packs: {packs}",
        f"- Components: {len(structure_map['components'])} at depth {structure_map['depth']}; "
        f"{len(structure_map['findings']['cycles'])} cycle(s)",
    ]
    if structure_map.get("truncated"):
        lines.append("- The walk stopped at the file cap; the map is partial.")
    unparsed = structure_map.get("unparsed", [])
    if unparsed:
        shown = ", ".join(f"{_code(item['path'])} ({_cell(item['reason'])})"
                          for item in unparsed[:MAX_UNPARSED_SHOWN])
        more = (f", and {len(unparsed) - MAX_UNPARSED_SHOWN} more in structure.json"
                if len(unparsed) > MAX_UNPARSED_SHOWN else "")
        lines.append(f"- Unparsed, so their symbols are missing: {shown}{more}")
    return lines


def _findings_section(structure_map, top: int) -> list:
    findings = structure_map["findings"]
    lines = ["", "## Findings", "", "| Finding | Count |", "| --- | --- |"]
    lines += [f"| {title} | {len(findings[key])} |" for key, title in FINDING_TITLES]
    for key, title in FINDING_TITLES:
        items = findings[key]
        if not items:
            continue
        lines += ["", f"### {title}", ""]
        if key == "names":
            rule_lines, unlisted = _name_rule_lines(items, max(0, min(NAME_EXAMPLES, top)))
            lines += [f"- {line}" for line in rule_lines]
            if unlisted:
                lines.append(f"- ... and {unlisted} more in structure.json")
            continue
        lines += [f"- {LINE_RENDERERS[key](item)}" for item in items[:top]]
        if len(items) > top:
            lines.append(f"- ... and {len(items) - top} more in structure.json")
    return lines


def _moves_section(moves: list, top: int) -> list:
    lines = ["", "## Proposed moves", ""]
    if not moves:
        return lines + ["No moves proposed."]
    lines += ["From the findings above; confirm each against the code before moving it.", ""]
    lines += [f"- {_code(', '.join(move['from']))} -> {_code(move['to'])} ({move['why']})"
              for move in moves[:top]]
    if len(moves) > top:
        lines.append(f"- ... and {len(moves) - top} more in structure.json")
    return lines


def _tree_section(structure_map, flagged) -> list:
    folders = defaultdict(lambda: {"files": 0, "symbols": 0, "flagged": 0, "roles": Counter()})
    for entry in structure_map["files"]:
        if entry["test"]:
            continue
        folder = entry["path"].rsplit("/", 1)[0] if "/" in entry["path"] else "."
        summary = folders[folder]
        summary["files"] += 1
        summary["symbols"] += sum(1 for symbol in entry["symbols"] if symbol["parent"] is None)
        summary["flagged"] += 1 if flagged["kinds"].get(entry["path"]) else 0
        summary["roles"][entry["home_role"] or "-"] += 1
    lines = ["", "## Tree", "", "| Folder | Role | Files | Symbols | Flagged |",
             "| --- | --- | --- | --- | --- |"]
    for folder in sorted(folders)[:MAX_TREE_ROWS]:
        summary = folders[folder]
        role = summary["roles"].most_common(1)[0][0]
        lines.append(f"| {_code(folder)} | {role} | {summary['files']} | {summary['symbols']} | "
                     f"{summary['flagged']} |")
    if len(folders) > MAX_TREE_ROWS:
        lines.append(f"| ... | | {len(folders) - MAX_TREE_ROWS} more folders | | |")
    return lines


def _metric(value) -> str:
    return "-" if value is None else f"{value:.2f}"


def _components_section(structure_map) -> list:
    components = structure_map["components"]
    lines = ["", "## Components", ""]
    if not components:
        return lines + ["No components found."]
    lines += ["| Component | Files | Ca | Ce | I | A | D |", "| --- | --- | --- | --- | --- | --- | --- |"]
    ranked = sorted(components, key=lambda item: (item["distance"] is None, -(item["distance"] or 0),
                                                  item["name"]))
    for item in ranked:
        lines.append(f"| {_code(item['name'])} | {item['files']} | {item['ca']} | {item['ce']} | "
                     f"{_metric(item['instability'])} | {_metric(item['abstractness'])} | "
                     f"{_metric(item['distance'])} |")
    edges = structure_map["edges"]
    if not edges:
        return lines
    degree = Counter()
    for edge in edges:
        degree[edge["from"]] += edge["count"]
        degree[edge["to"]] += edge["count"]
    shown = [name for name, _ in degree.most_common(MAX_GRAPH_NODES)]
    ids = {name: f"c{index}" for index, name in enumerate(shown)}
    in_cycle = {name for cycle in structure_map["findings"]["cycles"] for name in cycle["components"]}
    lines += ["", "```mermaid", "graph LR"]
    lines += [f'  {ids[name]}["{name}"]' for name in shown]
    for edge in edges:
        if edge["from"] in ids and edge["to"] in ids:
            arrow = "-.->" if edge["from"] in in_cycle and edge["to"] in in_cycle else "-->"
            lines.append(f"  {ids[edge['from']]} {arrow}|{edge['count']}| {ids[edge['to']]}")
    lines.append("```")
    if len(degree) > MAX_GRAPH_NODES:
        lines.append(f"\nThe graph shows the {MAX_GRAPH_NODES} most connected components; "
                     "dotted arrows are inside a cycle.")
    return lines


def _symbols_cell(entry, flagged) -> str:
    marked = flagged["symbols"].get(entry["path"], set())
    top = [symbol for symbol in entry["symbols"] if symbol["parent"] is None]
    names = [_code(symbol["name"]) + (" !" if symbol["name"] in marked else "")
             for symbol in top[:MAX_SYMBOLS_PER_ROW]]
    if len(top) > MAX_SYMBOLS_PER_ROW:
        names.append(f"+{len(top) - MAX_SYMBOLS_PER_ROW}")
    return ", ".join(names) or "-"


def _files_section(structure_map, flagged) -> list:
    lines = ["", "## Files", "", "| File | Role | Symbols | Purpose |", "| --- | --- | --- | --- |"]
    for entry in sorted(structure_map["files"], key=lambda item: item["path"]):
        if entry["test"]:
            continue
        lines.append(f"| {_code(entry['path'])} | {entry['role']} | {_symbols_cell(entry, flagged)} | "
                     f"{_cell(entry['purpose']) or '-'} |")
    return lines


def render_markdown(structure_map: dict, top: int = 25) -> str:
    """The full structure map, most important section first."""
    flagged = _flagged(structure_map)
    lines = (_header(structure_map) + _findings_section(structure_map, top)
             + _moves_section(structure_map.get("moves", []), top)
             + _tree_section(structure_map, flagged) + _components_section(structure_map)
             + _files_section(structure_map, flagged))
    return "\n".join(lines) + "\n"


def _under(path: str, prefix) -> bool:
    return prefix is None or path == prefix or path.startswith(prefix + "/")


def finding_paths(key: str, finding) -> list:
    """The paths a finding names: files, and folders or components with a trailing slash."""
    if key in {"duplicates", "name_clashes"}:
        return [member["path"] for member in finding["members"]]
    if key == "synonyms":
        return [entry["path"] for entries in finding["verbs"].values() for entry in entries]
    if key == "cycles":
        return [name + "/" for name in finding["components"]]
    if key in FOLDER_FINDINGS:
        return [finding["folder"] + "/"]
    return [finding["path"]]


def render_summary(structure_map: dict, path_filter=None) -> str:
    """A terminal summary; with path_filter, only that folder's files and findings."""
    prefix = None
    if path_filter:
        prefix = path_filter.replace("\\", "/").strip("/")
        while prefix.startswith("./"):
            prefix = prefix[2:]
    findings = {
        key: [item for item in structure_map["findings"][key]
              if any(_under(path.rstrip("/"), prefix) for path in finding_paths(key, item))]
        for key, _ in FINDING_TITLES
    }
    counts = ", ".join(f"{title.lower()} {len(findings[key])}" for key, title in SUMMARY_TITLES)
    scope = (f" (under {prefix})" if prefix else "") + \
        (" (changed files only)" if structure_map.get("changed") is not None else "")
    lines = [
        "Structure map (evidence for judgement, not a verdict)",
        "",
        f"  Files     : {structure_map['file_count']} source, {structure_map['test_file_count']} test, "
        f"{structure_map['symbol_count']} top-level symbols",
        f"  Packs     : {', '.join(structure_map['packs']) or 'none (generic conventions only)'}",
        f"  Findings  : {counts}{scope}",
    ]
    unparsed = [item["path"] for item in structure_map.get("unparsed", []) if _under(item["path"], prefix)]
    if unparsed:
        more = f" and {len(unparsed) - SUMMARY_PER_KIND} more" if len(unparsed) > SUMMARY_PER_KIND else ""
        lines.append(f"  Unparsed  : {', '.join(unparsed[:SUMMARY_PER_KIND])}{more} "
                     "(their symbols are missing)")
    for key, title in SUMMARY_TITLES:
        items = findings[key]
        if not items:
            continue
        lines += ["", f"  {title}"]
        if key == "names":
            rule_lines, unlisted = _name_rule_lines(items, NAME_EXAMPLES)
            lines += [f"    {line.replace('`', '')}" for line in rule_lines]
            if unlisted:
                lines.append(f"    ... and {unlisted} more")
            continue
        lines += [f"    {LINE_RENDERERS[key](item).replace('`', '')}" for item in items[:SUMMARY_PER_KIND]]
        if len(items) > SUMMARY_PER_KIND:
            lines.append(f"    ... and {len(items) - SUMMARY_PER_KIND} more")
    if prefix:
        flagged = _flagged(structure_map)
        rows = [entry for entry in sorted(structure_map["files"], key=lambda item: item["path"])
                if not entry["test"] and _under(entry["path"], prefix)]
        lines += ["", f"  Files under {prefix}"]
        for entry in rows:
            symbols = _symbols_cell(entry, flagged).replace("`", "")
            purpose = f" -- {entry['purpose']}" if entry["purpose"] else ""
            lines.append(f"    {entry['path']} [{entry['role']}] {symbols}{purpose}")
        if not rows:
            lines.append("    (no source files)")
    lines += ["", "  Save the full map with --write (.clean/structure.md and .clean/structure.json)."]
    return "\n".join(lines)
