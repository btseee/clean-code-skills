#!/usr/bin/env bash
# Maintenance tool for this repository (contributors only; users never need it).
# Propagates the version in VERSION into every stamped location, then mirrors
# the managed block from templates/agent-block.md into all adapter files.
# Workflow: edit VERSION and/or the template, run this script, then validate.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT_DIR/templates/agent-block.md"

VERSION="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
[[ -n "$VERSION" ]] || { printf 'ERROR: VERSION file is empty\n' >&2; exit 1; }

# 1. Stamp the version everywhere it appears.
sed -i "s/^<!-- clean-code-skills:begin v.* -->$/<!-- clean-code-skills:begin v$VERSION -->/" "$TEMPLATE"
sed -i "s/^  version: \".*\"$/  version: \"$VERSION\"/" "$ROOT_DIR/skills/clean-code/SKILL.md"
for manifest in .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json gemini-extension.json; do
  sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/g" "$ROOT_DIR/$manifest"
done
printf 'STAMPED: version %s\n' "$VERSION"

# 2. Mirror the managed block into every adapter file.
adapters=(
  "CLAUDE.md"
  "AGENTS.md"
  "GEMINI.md"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  ".cursor/rules/clean-code.mdc"
  ".windsurf/rules/clean-code.md"
  ".clinerules/clean-code.md"
)

for adapter in "${adapters[@]}"; do
  file="$ROOT_DIR/$adapter"
  [[ -f "$file" ]] || { printf 'ERROR: missing adapter %s\n' "$adapter" >&2; exit 1; }
  grep -q '^<!-- clean-code-skills:begin' "$file" || { printf 'ERROR: %s has no managed block\n' "$adapter" >&2; exit 1; }

  tmp="$(mktemp)"
  awk -v tpl="$TEMPLATE" '
    /^<!-- clean-code-skills:begin/ {
      while ((getline line < tpl) > 0) print line
      close(tpl)
      skipping = 1
      next
    }
    /^<!-- clean-code-skills:end -->$/ && skipping { skipping = 0; next }
    !skipping { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
  printf 'SYNCED: %s\n' "$adapter"
done

printf 'Sync complete. Run bash scripts/validate.sh to confirm.\n'
