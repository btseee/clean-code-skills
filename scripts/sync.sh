#!/usr/bin/env bash
# Maintenance tool for this repository (contributors only; users never need it).
# Propagates the version in VERSION into every stamped location, then mirrors
# the managed block from templates/agent-block.md into all adapter files.
# Workflow: edit VERSION and/or the template, run this script, then validate.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=install-lib.sh
source "$ROOT_DIR/scripts/install-lib.sh"
TARGET_DIR="$ROOT_DIR"

VERSION="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
[[ -n "$VERSION" ]] || { printf 'ERROR: VERSION file is empty\n' >&2; exit 1; }

# sed -i differs between GNU and BSD, so rewrite through a temp file instead.
stamp() {
  local tmp
  tmp="$(mktemp)"
  sed "$1" "$2" > "$tmp" && mv "$tmp" "$2"
}

# 1. Stamp the version everywhere it appears.
stamp "s/^${BEGIN_MARKER} v.* -->$/${BEGIN_MARKER} v$VERSION -->/" "$TEMPLATE"
stamp "s/^  version: \".*\"$/  version: \"$VERSION\"/" "$ROOT_DIR/skills/clean-code/SKILL.md"
for manifest in .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json gemini-extension.json; do
  stamp "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/g" "$ROOT_DIR/$manifest"
done
printf 'STAMPED: version %s\n' "$VERSION"

# 2. Mirror the managed block into every adapter file, with the installer's own merge.
# The adapter files are this repo's own copies of every project block and owned file.
for adapter in $(host_paths project block owned); do
  [[ -f "$ROOT_DIR/$adapter" ]] || { printf 'ERROR: missing adapter %s\n' "$adapter" >&2; exit 1; }
  merge_block "$ROOT_DIR/$adapter"
done

printf 'Sync complete. Run bash scripts/validate.sh to confirm.\n'
