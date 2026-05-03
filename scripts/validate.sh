#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

required_files=(
  "README.md"
  "CLAUDE.md"
  "GEMINI.md"
  "AGENTS.md"
  "EXAMPLES.md"
  "FRAMEWORKS.md"
  "CONTRIBUTING.md"
  "LICENSE"
  ".markdownlint.json"
  ".claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
  ".codex-plugin/plugin.json"
  ".cursor/rules/clean-code.mdc"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  "skills/clean-code/SKILL.md"
  "skills/clean-code/references/chapter-map.md"
  "skills/clean-code/references/framework-map.md"
  "skills/clean-code/references/review-checklist.md"
  "scripts/install.sh"
  "scripts/validate.sh"
)

for file in "${required_files[@]}"; do
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing $file"
done
pass "required files exist"

skill_file="$ROOT_DIR/skills/clean-code/SKILL.md"
[[ "$(sed -n '1p' "$skill_file")" == "---" ]] || fail "SKILL.md must start with front matter"
grep -q '^name: clean-code$' "$skill_file" || fail "SKILL.md name must be clean-code"
grep -q '^description: ' "$skill_file" || fail "SKILL.md needs description"
grep -q '^license: MIT$' "$skill_file" || fail "SKILL.md needs MIT license field"
sed -n '2,8p' "$skill_file" | grep -q '^---$' || fail "SKILL.md front matter must close near the top"
pass "skill front matter is valid"

cursor_rule="$ROOT_DIR/.cursor/rules/clean-code.mdc"
[[ "$(sed -n '1p' "$cursor_rule")" == "---" ]] || fail "Cursor rule must start with front matter"
grep -q '^alwaysApply: true$' "$cursor_rule" || fail "Cursor rule must always apply"
pass "Cursor rule front matter is valid"

copilot_instruction="$ROOT_DIR/.github/instructions/clean-code.instructions.md"
[[ "$(sed -n '1p' "$copilot_instruction")" == "---" ]] || fail "Copilot instruction must start with front matter"
grep -q '^applyTo: "\*\*/\*"$' "$copilot_instruction" || fail "Copilot instruction must apply to all files"
pass "Copilot instruction front matter is valid"

if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "$ROOT_DIR/.claude-plugin/plugin.json" >/dev/null
  python3 -m json.tool "$ROOT_DIR/.claude-plugin/marketplace.json" >/dev/null
  python3 -m json.tool "$ROOT_DIR/.codex-plugin/plugin.json" >/dev/null
  python3 -m json.tool "$ROOT_DIR/.markdownlint.json" >/dev/null
  pass "JSON files parse"
else
  printf 'WARN: python3 unavailable; skipped JSON parse check\n' >&2
fi

bash -n "$ROOT_DIR/scripts/install.sh"
bash -n "$ROOT_DIR/scripts/validate.sh"
pass "shell scripts parse"

install_tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$install_tmp_dir"
}
trap cleanup EXIT

bash "$ROOT_DIR/scripts/install.sh" --target "$install_tmp_dir" all >/dev/null
installed_files=(
  "CLAUDE.md"
  "GEMINI.md"
  "AGENTS.md"
  ".cursor/rules/clean-code.mdc"
  ".github/copilot-instructions.md"
  ".github/instructions/clean-code.instructions.md"
  "skills/clean-code/SKILL.md"
  "skills/clean-code/references/chapter-map.md"
  "skills/clean-code/references/framework-map.md"
  "skills/clean-code/references/review-checklist.md"
  ".github/skills/clean-code/SKILL.md"
  ".github/skills/clean-code/references/chapter-map.md"
  ".github/skills/clean-code/references/framework-map.md"
  ".github/skills/clean-code/references/review-checklist.md"
)

for file in "${installed_files[@]}"; do
  [[ -f "$install_tmp_dir/$file" ]] || fail "installer did not create $file"
done
pass "installer all profile works"

while IFS= read -r file; do
  if LC_ALL=C grep -q $'\r' "$file"; then
    fail "CRLF line ending found in ${file#$ROOT_DIR/}"
  fi

  if [[ -s "$file" && "$(tail -c 1 "$file" | wc -l)" -eq 0 ]]; then
    fail "missing final newline in ${file#$ROOT_DIR/}"
  fi
done < <(find "$ROOT_DIR" -path "$ROOT_DIR/.git" -prune -o -type f -print)
pass "line endings are LF"

pass "clean-code-skills repository is valid"
