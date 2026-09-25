# Configuring Clean Code Skills

Everything here is optional: the skill works with no configuration and no tooling. Configuration is
how you tell every agent, in every session, what this project has already decided.

## The `.clean/` Directory

The mechanism that lets a memoryless session resume. `/clean-code init` and `/clean-code audit`
create it; a plain session reads it and offers to persist at the end. Templates live in
`skills/clean-code/assets/templates/`. Add `.clean/` to `.gitignore` unless you want the design
intent committed; `architecture.md` is the file most worth committing, because it drives a check in
CI.

| File | Holds | Written by |
| --- | --- | --- |
| `context.json` | detected stack, frameworks, the packs they need, test command, layout, dependencies with versions, plus the interview's `confirmed` answers | `detect_stack.py --write` (merges — `confirmed` survives) and the `init` interview |
| `architecture.md` | declared layers and allowed dependencies; its absence means framework-first | `init` or `audit` when you opt in, or you |
| `roles.md` | your project's own role conventions and confirmed placement exceptions | `init`, `audit`, or you |
| `decisions.md` | decisions and their reasoning, append-only | any session that made a real choice |
| `ledger.md` | the audit's coverage checklist and findings, then cleanup progress | `audit` first, cleanup sessions after |
| `structure.md`, `structure.json` | every source file's symbols, role, and purpose; placement, duplication, naming, and cycle findings; families, junk drawers, flat folders, unreferenced and comment-heavy files; a **Proposed moves** section; component metrics | `map_structure.py --write`; never edit by hand |

## Declaring Layers

Without a declaration the skill is **framework-first**: it follows each framework pack's idiomatic
structure. Declare layers when you want the Dependency Rule enforced strictly. List them innermost
first in `.clean/architecture.md`, in a fenced block the tools read:

````markdown
```clean-architecture
layer domain         = src/domain/**
layer application    = src/application/**
layer adapter        = src/adapter/**
layer infrastructure = src/infrastructure/**

# Optional. The default is inward-only, so most projects need none.
# allow infrastructure -> domain
```
````

A layer may depend on itself and on any layer declared before it, and on nothing declared after it.
`check_boundaries.py` enforces the declaration and exits non-zero on a violation — or with exit code
2 when the globs match no files, because a check that checks nothing is worse than none. Each
framework pack's **Layers** section suggests a declaration for that stack.

## Declaring Roles

A role is a kind of responsibility with a conventional home: middleware lives with middleware.
`map_structure.py` reads role conventions from `clean-roles` blocks — the generic ones in
`skills/clean-code/references/framework-map.md`, one per framework pack, and yours in
`.clean/roles.md`, which is read first:

````markdown
```clean-roles
role middleware = src/http/middleware/**
signal middleware = implements\s+RequestInterceptor
name job [ts] = Job$
allow controller = middleware
accept src/legacy/**
accept src/services/auth.ts = requireSession
entry src/pages/sitemap.ts
ignore-name = ^(handler|config)$
```
````

`role` names a home by glob, `name` recognizes a role from a symbol's name, `signal` from its
decorators, base types, or signature, `allow` lets a home hold symbols of other roles (a React
context file holds its Provider and hook), `entry` lists files a framework loads by name or place
(a sitemap, Django's `apps.py`, a Laravel seeder) so the unreferenced finding never flags them and
a folder holding only such files is no junk drawer, and `ignore-name` leaves names out of the
name-clash, synonym, and naming findings. Files a manifest runs — pyproject `[project.scripts]`,
`[project.gui-scripts]`, and `[project.entry-points.*]` targets, package.json `bin`, `main`,
`module`, and `exports` paths — count as entries without an `entry` line. An optional
`[ext, ext]` list limits a `name` or `signal` rule to those file types.
Signals beat names, and the most specific home glob wins, so a rule of your own does not silence a
pack's finding; record a deliberate exception with `accept`: a glob alone covers whole files, and
`= symbol, ...` covers only those symbols. Accepted code gets no misplaced, mixed, naming, or
organization finding; add the reason to `.clean/decisions.md`.

## Naming And Organization Findings

`map_structure.py` also reports what a name or a folder gets wrong, each a `names` or an
organization finding, evidence for judgement, never a verdict. Each label below is the finding's
key in `.clean/structure.json`:

- **`names`**: a class, function, method, variable, or parameter that breaks a Clean Code naming
  rule — vague, encoded (Hungarian, a stray `I` prefix), numbered (`_v2`, `data2`), a noise word
  (`Manager`, `Helper`), a verb-named class, too short, off the language's casing convention, or a
  file whose one public type has an unrelated name — each citing the rule it breaks (N1, N3, N4,
  N5, N6, G17, G24).
- **`family`**: three or more files in one folder that share a name and import each other, proposed
  as a folder named for it.
- **`junk_drawer`**: a folder named for no concept (`utils`, `helpers`, `common`, `shared`, `misc`,
  and similar) holding production files, split by family and by role, or renamed when it holds one
  concept. A folder a convention names is left out: one holding only entries, the folder-glob home
  of the role it is named for (Rails' `app/helpers/`), or a `shared/` folder holding only
  components, directives, and pipes (an Angular shared UI module).
- **`flat_folder`**: a folder with more than fifteen production files, proposed to group by its
  families.
- **`unreferenced`**: a production file nothing imports and no role, entry point, `entry` line, or
  manifest target explains — "possibly unused" (G9), never a verdict; a file a framework finds by
  convention, annotation, or base type is not reported. Before deleting one, search its path,
  module, and stem in manifests, Procfile, Dockerfile, CI files, HTML, and string imports.
- **`comment_heavy`**: a file whose comment lines are at least 40% of its non-blank lines and at
  least twenty in number — a candidate for the comment-cleanup workflow (`references/comments.md`);
  files in a `config/` folder at the top of the repository or of a project are left out.

`.clean/structure.md` collects the moves these findings imply under **Proposed moves**
(`source -> destination`), for an audit to confirm before the clean-up campaign's placement batch
acts on them. `map_structure.py --changed` limits every finding, including these, to files git
reports as changed against HEAD (or untracked), which is what `/clean-code review` runs against
the working tree.

## Compressing Instruction Files

`/clean-code compress [files]` (`references/compress.md`) rewrites a project's own instruction
files — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `DESIGN.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
and `.cursor`/`.github` rule files — tersely, since hosts load them on every turn. It keeps a
`<name>.original.md` backup until you delete it and never touches the clean-code managed block,
which the installer owns. `scripts/check_compression.py ORIGINAL COMPRESSED` proves the rewrite
kept every heading, code block, inline code span, URL, rule ID, and number, printing the token
reduction; exit 0 means nothing technical was lost.

## Hooks

`skills/clean-code/assets/hooks/pre-commit` is portable and needs no host support: it blocks a
commit only when the declared architecture is violated, or cannot be checked at all. Install it
with `cp skills/clean-code/assets/hooks/pre-commit .git/hooks/`. It finds the skill in any project
or global install location and probes for `python3`, `python`, or `py`.

`skills/clean-code/assets/hooks/claude-settings.json` adds two Claude Code hooks — merge it into
`.claude/settings.json` rather than replacing the file. At session start it prints the stack, the
packs to read, the declared layering, and the structure map's findings; after each edit it re-runs
the boundary check. Neither blocks an edit.

## Design Constraints

Worth knowing before you adopt it:

- **Budgets are enforced.** The always-loaded managed block stays under 750 tokens, `SKILL.md`
  under 1,500, and each pack under 2,000, because small models need the room for your code.
- **Only five frontmatter fields are portable** — `name`, `description`, `license`,
  `compatibility`, `metadata`. Hooks, slash commands, permissions, and memory are host-specific, so
  they live in `assets/` and `references/host-matrix.md` with a portable substitute for each.
- **The scripts are standard library only, with no network access.** They read your files and write
  only to `.clean/`. Their output is evidence for the agent's judgement, never a verdict.
- **The Boy Scout Rule is deliberately narrowed.** Agents clean the lines a task already touches and
  report the rest, because an agent applying the rule broadly produces unreviewable diffs.
- **No cross-host smoke test has been run.** Portability rests on conformance to the Agent Skills
  specification and the per-host audit in `host-matrix.md`, not on observed behavior in every host.
- **No book text is reproduced.** Principle names and their one-line formulations are the field's
  vocabulary; everything around them is written for this project.
