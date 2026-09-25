#!/usr/bin/env python3
"""The structure map as people and agents read it: .clean/structure.md and a summary.

structure.md is ordered so that a partial read still gets the most important part
first: the findings, then the folder tree, then the components, then one
greppable row per file. A model with a small context window reads the top and
greps the Files table for the paths it is about to change.

Standard library only.
"""

from __future__ import annotations

from collections import Counter, defaultdict

FINDING_TITLES = (
    ("misplaced", "Misplaced"),
    ("mixed", "Mixed"),
    ("duplicates", "Duplicates"),
    ("name_clashes", "Name clashes"),
    ("synonyms", "Synonyms"),
    ("names", "Names"),
    ("cycles", "Cycles"),
)
# The terminal summary keeps the order it had before names were reported, names last, so a
# reader comparing runs sees the same line with one more count.
SUMMARY_TITLES = (tuple((key, title) for key, title in FINDING_TITLES if key != "names")
                  + (("names", "Names"),))
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


def _where(item) -> str:
    return f"{item['path']}:{item['line']}"


def _destination(suggestion) -> str:
    """Where a finding sends code: a folder, a file, or its own file named like a pattern."""
    if not suggestion:
        return "its role's home"
    folder, _, name = suggestion.rpartition("/")
    if " " not in suggestion and any(mark in name for mark in "*?"):
        return f"its own file named like {_code(name)}" + (f" in {_code(folder + '/')}" if folder else "")
    return _code(suggestion)


def _misplaced_line(item) -> str:
    target = _destination(item["suggestion"])
    if item["symbol"] is None:
        return f"{_code(item['path'])} holds only {item['role']} code; move the file to {target}."
    home = f"a {item['home_role']} file" if item["home_role"] else "this file"
    return (f"{_code(_where(item))} {_code(item['symbol'])} is {item['role']} in {home}; "
            f"move it to {target}.")


def _mixed_line(item) -> str:
    parts = [f"{role} ({', '.join(_code(name) for name in names[:3])})"
             for role, names in item["roles"].items()]
    return f"{_code(item['path'])} mixes {', '.join(parts)}."


def _duplicate_line(item) -> str:
    members = ", ".join(f"{_code(_where(member))} {_code(member['symbol'])}"
                        for member in item["members"][:6])
    more = f", and {len(item['members']) - 6} more" if len(item["members"]) > 6 else ""
    return f"{item['kind']}, {item['lines']} lines: {members}{more}"


def _clash_line(item) -> str:
    members = ", ".join(_code(_where(member)) for member in item["members"][:6])
    return f"{_code(item['name'])} ({item['language']}): {members}"


def _synonym_line(item) -> str:
    verbs = ", ".join(f"{verb} x{len(entries)} ({_code(_where(entries[0]))})"
                      for verb, entries in item["verbs"].items())
    return f"{item['noun']} ({item['group']}): {verbs}"


def _cycle_line(item) -> str:
    names = item["components"]
    shown = " <-> ".join(_code(name) for name in names[:8])
    if len(names) > 8:
        shown += f" and {len(names) - 8} more"
    heaviest = sorted(item["edges"], key=lambda edge: -edge["count"])[:6]
    counts = ", ".join(f"{edge['from']} -> {edge['to']} x{edge['count']}" for edge in heaviest)
    more = f", {len(item['edges']) - 6} more edges" if len(item["edges"]) > 6 else ""
    return f"{shown} ({counts}{more})"


LINE_RENDERERS = {
    "misplaced": _misplaced_line, "mixed": _mixed_line, "duplicates": _duplicate_line,
    "name_clashes": _clash_line, "synonyms": _synonym_line, "cycles": _cycle_line,
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


def _flagged(data) -> dict:
    """path -> finding kinds that name the file, and the misplaced symbol names."""
    kinds = defaultdict(set)
    symbols = defaultdict(set)
    findings = data["findings"]
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


def _header(data) -> list:
    commit = f" at commit {_code(data['commit'])}" if data.get("commit") else ""
    languages = ", ".join(f"{name} {count}" for name, count in data["languages"].items()) or "none"
    packs = ", ".join(_code(pack) for pack in data["packs"]) or "none (generic conventions only)"
    lines = [
        "# Structure Map",
        "",
        f"Generated by `map_structure.py` on {data['generated']}{commit}. Evidence for judgement, "
        "not a verdict: read each finding, then decide. Regenerate when the commit differs from "
        "`git rev-parse --short HEAD`.",
        "",
        f"- Files: {data['file_count']} source, {data['test_file_count']} test; "
        f"{data['symbol_count']} top-level symbols; {languages}",
        f"- Packs: {packs}",
        f"- Components: {len(data['components'])} at depth {data['depth']}; "
        f"{len(data['findings']['cycles'])} cycle(s)",
    ]
    if data.get("truncated"):
        lines.append("- The walk stopped at the file cap; the map is partial.")
    unparsed = data.get("unparsed", [])
    if unparsed:
        shown = ", ".join(f"{_code(item['path'])} ({_cell(item['reason'])})"
                          for item in unparsed[:MAX_UNPARSED_SHOWN])
        more = (f", and {len(unparsed) - MAX_UNPARSED_SHOWN} more in structure.json"
                if len(unparsed) > MAX_UNPARSED_SHOWN else "")
        lines.append(f"- Unparsed, so their symbols are missing: {shown}{more}")
    return lines


def _findings_section(data, top: int) -> list:
    findings = data["findings"]
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


def _tree_section(data, flagged) -> list:
    folders = defaultdict(lambda: {"files": 0, "symbols": 0, "flagged": 0, "roles": Counter()})
    for entry in data["files"]:
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


def _components_section(data) -> list:
    components = data["components"]
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
    edges = data["edges"]
    if not edges:
        return lines
    degree = Counter()
    for edge in edges:
        degree[edge["from"]] += edge["count"]
        degree[edge["to"]] += edge["count"]
    shown = [name for name, _ in degree.most_common(MAX_GRAPH_NODES)]
    ids = {name: f"c{index}" for index, name in enumerate(shown)}
    in_cycle = {name for cycle in data["findings"]["cycles"] for name in cycle["components"]}
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


def _files_section(data, flagged) -> list:
    lines = ["", "## Files", "", "| File | Role | Symbols | Purpose |", "| --- | --- | --- | --- |"]
    for entry in sorted(data["files"], key=lambda item: item["path"]):
        if entry["test"]:
            continue
        lines.append(f"| {_code(entry['path'])} | {entry['role']} | {_symbols_cell(entry, flagged)} | "
                     f"{_cell(entry['purpose']) or '-'} |")
    return lines


def render_markdown(data: dict, top: int = 25) -> str:
    """The full structure map, most important section first."""
    flagged = _flagged(data)
    lines = (_header(data) + _findings_section(data, top) + _tree_section(data, flagged)
             + _components_section(data) + _files_section(data, flagged))
    return "\n".join(lines) + "\n"


def _under(path: str, prefix) -> bool:
    return prefix is None or path == prefix or path.startswith(prefix + "/")


def _finding_paths(key: str, item) -> list:
    if key in {"duplicates", "name_clashes"}:
        return [member["path"] for member in item["members"]]
    if key == "synonyms":
        return [entry["path"] for entries in item["verbs"].values() for entry in entries]
    if key == "cycles":
        return [name + "/" for name in item["components"]]
    return [item["path"]]


def render_summary(data: dict, path_filter=None) -> str:
    """A terminal summary; with path_filter, only that folder's files and findings."""
    prefix = None
    if path_filter:
        prefix = path_filter.replace("\\", "/").strip("/")
        while prefix.startswith("./"):
            prefix = prefix[2:]
    findings = {
        key: [item for item in data["findings"][key]
              if any(_under(path.rstrip("/"), prefix) for path in _finding_paths(key, item))]
        for key, _ in FINDING_TITLES
    }
    counts = ", ".join(f"{title.lower()} {len(findings[key])}" for key, title in SUMMARY_TITLES)
    lines = [
        "Structure map (evidence for judgement, not a verdict)",
        "",
        f"  Files     : {data['file_count']} source, {data['test_file_count']} test, "
        f"{data['symbol_count']} top-level symbols",
        f"  Packs     : {', '.join(data['packs']) or 'none (generic conventions only)'}",
        f"  Findings  : {counts}" + (f" (under {prefix})" if prefix else ""),
    ]
    unparsed = [item["path"] for item in data.get("unparsed", []) if _under(item["path"], prefix)]
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
        flagged = _flagged(data)
        rows = [entry for entry in sorted(data["files"], key=lambda item: item["path"])
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
