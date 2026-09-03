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
One of the three optional Python scripts a session runs against a project: stack detection, smell measurement, or the boundary check.
_Avoid_: tool, helper

**Project walker**:
The one rule for which files count as the project when a scanner walks it: skip lists, the file cap, and what a test path looks like.

**Layering**:
The layers a project declared innermost first, and the dependency directions allowed between them.
_Avoid_: layer config, architecture rules

**Verdict**:
What the boundary check says about one import: it points inward, it points outward, or it cannot be placed in any declared layer.
