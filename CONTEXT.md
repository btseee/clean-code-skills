# clean-code-skills

One skill, the clean-code rules, delivered to many AI coding hosts. This context names the pieces that carry the skill from this repository into a project, and the terms the installers, sync, and validator share.

## Language

### Delivery

**Host**:
An AI coding tool that reads instruction files or skill folders from a project or a home directory (Claude Code, Codex CLI, Cursor, Copilot, Gemini CLI, and so on).
_Avoid_: client, agent (when you mean the tool), platform

**Profile**:
The name a user gives the installer to install for one host or a bundle of hosts, such as `claude`, `cursor`, or `all`.
_Avoid_: target, preset, mode

**Scope**:
Where a profile installs: `project` for one repository, `global` for the user's home directory.

**Host table**:
The single list of every profile, its scope, and the paths it installs, in `templates/hosts.tsv`.
_Avoid_: profile map, detection table, adapter list

**Managed block**:
The rules text inserted into a shared instruction file between a begin marker that carries the version and a fixed end marker; at most one per file, and only the installer edits it.
_Avoid_: rules block, snippet, section

**Adapter file**:
This repository's own copy of a host's instruction file, carrying the managed block so the repository is also an installed example.
_Avoid_: mirror, host file

**Owned file**:
A dedicated instruction file the package creates and replaces whole, such as a Cursor rule; never merged.

**Skill folder**:
A copy of `skills/clean-code/` placed where a host discovers skills.
_Avoid_: skill dir, skill root (that is the host's parent directory)

### Skill runtime

**Scanner**:
One of the four optional Python scripts a session runs against a project: stack detection, the structure map, smell measurement, or the boundary check.
_Avoid_: tool, helper

**Project walker**:
The one rule for which files count as the project when a scanner walks it: skip lists, the file cap, what a test path looks like, and which files a generator owns.

**Pack**:
A short, strict reference for one language (a language pack) or one framework (a framework pack), loaded only when the project uses it.
_Avoid_: guide, module, plugin

**Pack index**:
The fenced `clean-packs` block in `framework-map.md` that maps each detected language and framework label to its packs.

**Layering**:
The layers a project declared innermost first, and the dependency directions allowed between them. Without one, the skill is framework-first: it follows the framework pack's structure.
_Avoid_: layer config, architecture rules

**Verdict**:
What the boundary check says about one import: it points inward, it points outward, or it cannot be placed in any declared layer.

**Role**:
A kind of responsibility with a conventional home — middleware, controller, repository — declared in `clean-roles` blocks.
_Avoid_: type, category, layer

**Home role**:
The role a file's location promises, from the most specific matching `role` glob. A symbol whose own role differs from its file's home role is misplaced.

**Structure map**:
`.clean/structure.md` and `.clean/structure.json`: every source file's symbols, role, and purpose, with the findings and component metrics. A generated cache, never hand-edited.
_Avoid_: inventory, index (that is the pack index)

**Finding**:
One piece of evidence the structure map reports — misplaced, mixed, duplicate, name clash, synonyms, cycle, naming, or organization finding. Evidence for judgement, never a verdict.

**Naming finding**:
A name a Clean Code rule flags — vague, encoded, numbered, a noise word, a verb-named class, too short, off the language's casing convention, or a file mismatched with its one public type — each citing the rule it breaks.

**Family**:
Three or more files in one folder that share a leading name token and import each other; proposed as a folder named for the token.
_Avoid_: group, cluster

**Junk drawer**:
A folder named for no concept (`utils`, `helpers`, `common`, and similar) holding production files; split by family and by role, or renamed when it holds one concept.

**Flat folder**:
A folder holding more production files than the map's limit, with no grouping; proposed to group by its families.

**Move plan**:
The **Proposed moves** section of the structure map: concrete `source -> destination` moves a family, a junk drawer, or a misplaced symbol implies, for an audit to confirm before the clean-up campaign's placement batch acts on them.

**Entry directive**:
A `clean-roles` line naming files a framework loads without an import (a sitemap, a seeder); the unreferenced finding never calls such a file possibly unused, and the junk-drawer finding skips a folder holding only such files. Files a manifest runs (pyproject scripts, package.json `bin`) are entries without one.

**Agent smell**:
One of ten failure patterns specific to AI-generated code (A1-A10, `review-checklist.md`), each with a signal and a response, cited beside the book's smell IDs.

**Risk level**:
LOW, MEDIUM, or HIGH, set from a change's scope, blast radius, uncertainty, and reversibility; each level names the checks it owes before completion.

**Component**:
For the metrics, a folder prefix of a fixed depth: the practical stand-in for a release unit in application code.
