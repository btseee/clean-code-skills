#!/usr/bin/env python3
"""How components depend on each other: coupling, instability, abstractness, cycles.

A component here is a folder prefix of a fixed depth -- the practical stand-in
for a release unit in application code. The metrics are the component principles
made measurable:

    Ca  afferent coupling: files outside that depend on the component
    Ce  efferent coupling: files outside that the component depends on
    I   instability  = Ce / (Ca + Ce)       0 is maximally stable
    A   abstractness = abstract types / types
    D   distance     = |A + I - 1|          0 is on the main sequence

A metric that cannot be computed is None, never zero: a folder of functions has
no abstractness, and pretending it is 0 would put it in the zone of pain.

Standard library only.
"""

from __future__ import annotations

from collections import Counter, defaultdict


def component_of(path: str, depth: int) -> str:
    """The first depth folders of path; "." for a file at the root."""
    folders = path.split("/")[:-1]
    if not folders:
        return "."
    return "/".join(folders[:depth])


def _ratio(numerator: int, denominator: int):
    return round(numerator / denominator, 3) if denominator else None


def _strongly_connected(graph: dict) -> list:
    """Sets of two or more components that reach each other (Tarjan, iterative)."""
    counter = 0
    indices = {}
    lowlinks = {}
    stack = []
    on_stack = set()
    found = []
    for start in sorted(graph):
        if start in indices:
            continue
        indices[start] = lowlinks[start] = counter
        counter += 1
        stack.append(start)
        on_stack.add(start)
        work = [(start, iter(sorted(graph.get(start, ()))))]
        while work:
            node, children = work[-1]
            descended = False
            for child in children:
                if child not in indices:
                    indices[child] = lowlinks[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(graph.get(child, ())))))
                    descended = True
                    break
                if child in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[child])
            if descended:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                lowlinks[parent] = min(lowlinks[parent], lowlinks[node])
            if lowlinks[node] == indices[node]:
                members = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    members.append(member)
                    if member == node:
                        break
                if len(members) > 1:
                    found.append(sorted(members))
    return sorted(found)


def analyze(file_imports: dict, type_counts: dict, depth: int) -> dict:
    """Components, the edges between them, and their cycles.

    file_imports maps each non-test source file to the project files it imports;
    type_counts maps a file to (types, abstract types).
    """
    members = defaultdict(set)
    for path in set(file_imports) | set(type_counts):
        members[component_of(path, depth)].add(path)

    edge_counts = Counter()
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for source, targets in file_imports.items():
        source_component = component_of(source, depth)
        for target in targets:
            target_component = component_of(target, depth)
            members[target_component].add(target)
            if target_component == source_component:
                continue
            edge_counts[(source_component, target_component)] += 1
            outgoing[source_component].add(target)
            incoming[target_component].add(source)

    components = []
    for name in sorted(members):
        ca, ce = len(incoming[name]), len(outgoing[name])
        types = sum(type_counts.get(path, (0, 0))[0] for path in members[name])
        abstract = sum(type_counts.get(path, (0, 0))[1] for path in members[name])
        instability = _ratio(ce, ca + ce)
        abstractness = _ratio(abstract, types)
        distance = (round(abs(abstractness + instability - 1), 3)
                    if instability is not None and abstractness is not None else None)
        components.append({
            "name": name, "files": len(members[name]), "types": types, "abstract_types": abstract,
            "ca": ca, "ce": ce, "instability": instability, "abstractness": abstractness,
            "distance": distance,
        })

    graph = defaultdict(set)
    for (source, target) in edge_counts:
        graph[source].add(target)
        graph.setdefault(target, set())
    cycles = []
    for cycle in _strongly_connected(graph):
        inside = set(cycle)
        cycles.append({
            "components": cycle,
            "edges": [{"from": source, "to": target, "count": count}
                      for (source, target), count in sorted(edge_counts.items())
                      if source in inside and target in inside],
        })

    edges = [{"from": source, "to": target, "count": count}
             for (source, target), count in sorted(edge_counts.items())]
    return {"components": components, "edges": edges, "cycles": cycles}
