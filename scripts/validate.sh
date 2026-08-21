#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT_DIR/templates/agent-block.md"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

# --- required files ---------------------------------------------------------

required_files=(
  "README.md"
  "CLAUDE.md"
  "GEMINI.md"
  "AGENTS.md"
  "EXAMPLES.md"
  "FRAMEWORKS.md"
  "CONTRIBUTING.md"
  "LICENSE"
  "VERSION"
  "gemini-extension.json"
  ".markdownlint.json"
  ".claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
  ".codex-plugin/plugin.json"
  ".cursor/rules/clean-code.mdc"
  ".windsurf/rules/clean-code.md"
  ".clinerules/clean-code.md"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  ".github/workflows/ci.yml"
  ".github/workflows/release.yml"
  "templates/agent-block.md"
  "skills/clean-code/SKILL.md"
  "skills/clean-code/references/chapter-map.md"
  "skills/clean-code/references/framework-map.md"
  "skills/clean-code/references/review-checklist.md"
  "skills/clean-code/references/project-refactor.md"
  "scripts/install.sh"
  "scripts/install.ps1"
  "scripts/remote-install.sh"
  "scripts/remote-install.ps1"
  "scripts/sync.sh"
  "scripts/validate.sh"
  "scripts/validate.ps1"
)

for file in "${required_files[@]}"; do
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing $file"
done
pass "required files exist"

# --- skill front matter ------------------------------------------------------

skill_file="$ROOT_DIR/skills/clean-code/SKILL.md"
[[ "$(sed -n '1p' "$skill_file")" == "---" ]] || fail "SKILL.md must start with front matter"
grep -q '^name: clean-code$' "$skill_file" || fail "SKILL.md name must be clean-code"
grep -q '^description: ' "$skill_file" || fail "SKILL.md needs description"
grep -q '^license: MIT$' "$skill_file" || fail "SKILL.md needs MIT license field"
sed -n '2,12p' "$skill_file" | grep -q '^---$' || fail "SKILL.md front matter must close near the top"
pass "skill front matter is valid"

# --- versions stay in sync ----------------------------------------------------

template_version="$(sed -n "s/^<!-- clean-code-skills:begin v\(.*\) -->$/\1/p" "$TEMPLATE")"
[[ -n "$template_version" ]] || fail "template begin marker must carry a version"

file_version="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
[[ "$file_version" == "$template_version" ]] || fail "VERSION file ($file_version) != template version ($template_version)"

skill_version="$(sed -n 's/^  version: "\(.*\)"$/\1/p' "$skill_file")"
[[ "$skill_version" == "$template_version" ]] || fail "SKILL.md metadata version ($skill_version) != template version ($template_version)"

for manifest in ".claude-plugin/plugin.json" ".codex-plugin/plugin.json" "gemini-extension.json"; do
  grep -q "\"version\": \"$template_version\"" "$ROOT_DIR/$manifest" || fail "$manifest version != $template_version"
done
grep -q "\"version\": \"$template_version\"" "$ROOT_DIR/.claude-plugin/marketplace.json" || fail "marketplace.json version != $template_version"
pass "versions are in sync ($template_version)"

# --- managed block stays identical across adapters ----------------------------

block_files=(
  "CLAUDE.md"
  "AGENTS.md"
  "GEMINI.md"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  ".cursor/rules/clean-code.mdc"
  ".windsurf/rules/clean-code.md"
  ".clinerules/clean-code.md"
)

extract_block() {
  awk '/^<!-- clean-code-skills:begin/{inside=1} inside{print} /^<!-- clean-code-skills:end -->$/{inside=0}' "$1"
}

template_block="$(extract_block "$TEMPLATE")"
[[ -n "$template_block" ]] || fail "template has no managed block"

for file in "${block_files[@]}"; do
  file_block="$(extract_block "$ROOT_DIR/$file")"
  [[ "$file_block" == "$template_block" ]] || fail "$file managed block drifted from templates/agent-block.md"
done
pass "managed block is identical in all adapter files"

# --- tool front matter ---------------------------------------------------------

cursor_rule="$ROOT_DIR/.cursor/rules/clean-code.mdc"
[[ "$(sed -n '1p' "$cursor_rule")" == "---" ]] || fail "Cursor rule must start with front matter"
grep -q '^alwaysApply: true$' "$cursor_rule" || fail "Cursor rule must always apply"
pass "Cursor rule front matter is valid"

copilot_instruction="$ROOT_DIR/.github/instructions/clean-code.instructions.md"
[[ "$(sed -n '1p' "$copilot_instruction")" == "---" ]] || fail "Copilot instruction must start with front matter"
grep -q '^applyTo: "\*\*/\*"$' "$copilot_instruction" || fail "Copilot instruction must apply to all files"
pass "Copilot instruction front matter is valid"

# --- JSON and shell syntax ------------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  PYTHON=""
fi

if [[ -n "$PYTHON" ]]; then
  "$PYTHON" -m json.tool "$ROOT_DIR/.claude-plugin/plugin.json" >/dev/null
  "$PYTHON" -m json.tool "$ROOT_DIR/.claude-plugin/marketplace.json" >/dev/null
  "$PYTHON" -m json.tool "$ROOT_DIR/.codex-plugin/plugin.json" >/dev/null
  "$PYTHON" -m json.tool "$ROOT_DIR/gemini-extension.json" >/dev/null
  "$PYTHON" -m json.tool "$ROOT_DIR/.markdownlint.json" >/dev/null
  pass "JSON files parse"
else
  printf 'WARN: python unavailable; skipped JSON parse check\n' >&2
fi

bash -n "$ROOT_DIR/scripts/install.sh"
bash -n "$ROOT_DIR/scripts/remote-install.sh"
bash -n "$ROOT_DIR/scripts/sync.sh"
bash -n "$ROOT_DIR/scripts/validate.sh"
pass "shell scripts parse"

# --- installer behavior -----------------------------------------------------------

install_tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$install_tmp_dir"
}
trap cleanup EXIT

# Pre-existing user content in a shared file must survive the merge.
printf '# My Project\n\nLocal agent notes that must survive.\n' > "$install_tmp_dir/AGENTS.md"

bash "$ROOT_DIR/scripts/install.sh" --target "$install_tmp_dir" all >/dev/null

installed_files=(
  "CLAUDE.md"
  "GEMINI.md"
  "AGENTS.md"
  ".cursor/rules/clean-code.mdc"
  ".windsurf/rules/clean-code.md"
  ".clinerules/clean-code.md"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  "skills/clean-code/SKILL.md"
  "skills/clean-code/references/chapter-map.md"
  "skills/clean-code/references/framework-map.md"
  "skills/clean-code/references/review-checklist.md"
  "skills/clean-code/references/project-refactor.md"
  ".claude/skills/clean-code/SKILL.md"
  ".github/skills/clean-code/SKILL.md"
)

for file in "${installed_files[@]}"; do
  [[ -f "$install_tmp_dir/$file" ]] || fail "installer did not create $file"
done
pass "installer all profile works"

grep -q 'Local agent notes that must survive.' "$install_tmp_dir/AGENTS.md" || fail "installer clobbered existing AGENTS.md content"
[[ "$(grep -c 'clean-code-skills:begin' "$install_tmp_dir/AGENTS.md")" -eq 1 ]] || fail "AGENTS.md should contain exactly one managed block"
pass "merge preserves existing content"

bash "$ROOT_DIR/scripts/install.sh" --target "$install_tmp_dir" all >/dev/null
[[ "$(grep -c 'clean-code-skills:begin' "$install_tmp_dir/AGENTS.md")" -eq 1 ]] || fail "re-install duplicated the managed block"
[[ "$(grep -c 'clean-code-skills:begin' "$install_tmp_dir/CLAUDE.md")" -eq 1 ]] || fail "re-install duplicated the CLAUDE.md block"
pass "re-install is idempotent"

detect_output="$(bash "$ROOT_DIR/scripts/install.sh" --target "$install_tmp_dir" --detect)"
printf '%s\n' "$detect_output" | grep -q 'Detected profiles: .*claude' || fail "--detect did not find the claude profile"
printf '%s\n' "$detect_output" | grep -q 'Detected profiles: .*cursor' || fail "--detect did not find the cursor profile"
[[ "$(grep -c 'clean-code-skills:begin' "$install_tmp_dir/AGENTS.md")" -eq 1 ]] || fail "--detect update duplicated the managed block"
pass "detect updates exactly what is installed"

bash "$ROOT_DIR/scripts/install.sh" --target "$install_tmp_dir" --uninstall all >/dev/null
grep -q 'Local agent notes that must survive.' "$install_tmp_dir/AGENTS.md" || fail "uninstall removed user content from AGENTS.md"
if grep -rq 'clean-code-skills:begin' "$install_tmp_dir" 2>/dev/null; then
  fail "uninstall left managed markers behind"
fi
[[ ! -e "$install_tmp_dir/skills/clean-code" ]] || fail "uninstall left skills/clean-code behind"
[[ ! -e "$install_tmp_dir/.cursor/rules/clean-code.mdc" ]] || fail "uninstall left cursor rule behind"
pass "uninstall removes managed content and keeps user content"

fake_home="$install_tmp_dir/fake-home"
mkdir -p "$fake_home"
CLEAN_CODE_HOME="$fake_home" bash "$ROOT_DIR/scripts/install.sh" --global all >/dev/null
[[ -f "$fake_home/.claude/CLAUDE.md" ]] || fail "global install did not create ~/.claude/CLAUDE.md"
[[ -f "$fake_home/.claude/skills/clean-code/SKILL.md" ]] || fail "global install did not create ~/.claude/skills/clean-code"
[[ -f "$fake_home/.codex/AGENTS.md" ]] || fail "global install did not create ~/.codex/AGENTS.md"
[[ -f "$fake_home/.config/opencode/AGENTS.md" ]] || fail "global install did not create ~/.config/opencode/AGENTS.md"
[[ -f "$fake_home/.gemini/GEMINI.md" ]] || fail "global install did not create ~/.gemini/GEMINI.md"
[[ ! -e "$fake_home/.cursor" ]] || fail "global install must skip project-scoped cursor profile"
CLEAN_CODE_HOME="$fake_home" bash "$ROOT_DIR/scripts/install.sh" --global --detect >/dev/null
[[ "$(grep -c 'clean-code-skills:begin' "$fake_home/.claude/CLAUDE.md")" -eq 1 ]] || fail "global detect update duplicated the block"
CLEAN_CODE_HOME="$fake_home" bash "$ROOT_DIR/scripts/install.sh" --global --uninstall all >/dev/null
if grep -rq 'clean-code-skills:begin' "$fake_home" 2>/dev/null; then
  fail "global uninstall left managed markers behind"
fi
pass "global install, detect, and uninstall work"

# --- line endings -------------------------------------------------------------------

# Check the files this repository ships, not everything under the checkout: a working
# tree can also hold ignored caches, study material, and vendored third-party skills,
# none of which this repo controls.
list_repo_files() {
  if git -C "$ROOT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$ROOT_DIR" ls-files -z --cached --exclude-standard
  else
    find "$ROOT_DIR" \( -path "$ROOT_DIR/.git" -o -name "clean-code.md" -o -name "clean-code.pdf" -o -path "*/node_modules" \) -prune -o -type f -print0
  fi
}

while IFS= read -r -d '' file; do
  file="$ROOT_DIR/${file#$ROOT_DIR/}"
  [[ -f "$file" ]] || continue
  LC_ALL=C grep -Iq . "$file" 2>/dev/null || continue

  if LC_ALL=C grep -q $'\r' "$file"; then
    fail "CRLF line ending found in ${file#$ROOT_DIR/}"
  fi

  if [[ -s "$file" && "$(tail -c 1 "$file" | wc -l)" -eq 0 ]]; then
    fail "missing final newline in ${file#$ROOT_DIR/}"
  fi
done < <(list_repo_files)
pass "line endings are LF"

pass "clean-code-skills repository is valid"
