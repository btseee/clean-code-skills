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
  "skills/clean-code/references/architecture.md"
  "skills/clean-code/references/architecture-map.md"
  "skills/clean-code/references/principles.md"
  "skills/clean-code/references/smell-triage.md"
  "skills/clean-code/references/canon.md"
  "skills/clean-code/references/tests.md"
  "skills/clean-code/references/concurrency.md"
  "skills/clean-code/references/examples.md"
  "skills/clean-code/references/session-protocol.md"
  "skills/clean-code/references/new-project.md"
  "skills/clean-code/references/audit-report.md"
  "skills/clean-code/references/memory-protocol.md"
  "skills/clean-code/references/host-matrix.md"
  "skills/clean-code/scripts/detect_stack.py"
  "skills/clean-code/scripts/scan_repo.py"
  "skills/clean-code/scripts/check_boundaries.py"
  "skills/clean-code/assets/templates/architecture.md"
  "skills/clean-code/assets/templates/decisions.md"
  "skills/clean-code/assets/templates/ledger.md"
  "skills/clean-code/assets/hooks/pre-commit"
  "skills/clean-code/assets/hooks/claude-settings.json"
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

# --- skill budget -------------------------------------------------------------------

# The Agent Skills spec recommends keeping SKILL.md under 500 lines and roughly 5,000
# tokens, because hosts load the whole body on activation. Depth belongs in references/,
# which load on demand.
skill_file="$ROOT_DIR/skills/clean-code/SKILL.md"
skill_lines="$(wc -l < "$skill_file" | tr -d '[:space:]')"
skill_words="$(wc -w < "$skill_file" | tr -d '[:space:]')"
skill_tokens=$(( skill_words * 4 / 3 ))

[[ "$skill_lines" -le 500 ]] || fail "SKILL.md is $skill_lines lines; keep it under 500 and move depth into references/"
[[ "$skill_tokens" -le 5000 ]] || fail "SKILL.md is ~$skill_tokens tokens; keep it under 5000 and move depth into references/"
pass "SKILL.md is within budget ($skill_lines lines, ~$skill_tokens tokens)"

# --- skill scripts ------------------------------------------------------------------

# The scripts are optional accelerators that must run anywhere, so they may only use the
# standard library: a third-party import would make them fail on a clean machine.
if command -v python3 >/dev/null 2>&1; then
  SKILL_PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  SKILL_PYTHON=python
else
  SKILL_PYTHON=""
fi

if [[ -n "$SKILL_PYTHON" ]]; then
  for script in "$ROOT_DIR"/skills/clean-code/scripts/*.py; do
    "$SKILL_PYTHON" -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$script" \
      || fail "${script#$ROOT_DIR/} is not valid Python"
  done
  pass "skill scripts parse"

  "$SKILL_PYTHON" - "$ROOT_DIR" <<'PY' || fail "a skill script imports a third-party module; keep them standard-library only"
import ast
import pathlib
import sys

ALLOWED = {
    "argparse", "ast", "collections", "dataclasses", "difflib", "fnmatch",
    "functools", "hashlib", "io", "itertools", "json", "os", "pathlib", "re",
    "shutil", "subprocess", "sys", "tempfile", "textwrap", "time", "typing",
    "unicodedata", "__future__",
}

root = pathlib.Path(sys.argv[1]) / "skills" / "clean-code" / "scripts"
bad = []
for path in sorted(root.glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if name.split(".")[0] not in ALLOWED:
                bad.append(f"{path.name}: {name}")

if bad:
    print("third-party imports found: " + ", ".join(bad))
    sys.exit(1)
PY
  pass "skill scripts use only the standard library"
else
  printf 'WARN: python not found; skipping skill script checks\n'
fi

# --- portability of shipped skill content --------------------------------------------

# Skill content is read by many different agents. Naming one host's tools, or an absolute
# path from the author's machine, breaks it everywhere else.
while IFS= read -r -d '' shipped; do
  if LC_ALL=C grep -nE '(^|[^A-Za-z])(/Users/|/home/[a-z]|[A-Z]:\\\\)' "$shipped" >/dev/null; then
    fail "${shipped#$ROOT_DIR/} contains an absolute machine path; use paths relative to the skill or project root"
  fi
done < <(find "$ROOT_DIR/skills" "$ROOT_DIR/templates" -type f -name '*.md' -print0)
pass "shipped skill content has no absolute machine paths"

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

# `grep -U` forces binary mode. Without it, the grep shipped with Git for Windows
# strips CR before matching, so a plain `grep $'\r'` reports every file as clean and
# the whole check silently passes. Verify the detector against a known-CRLF fixture
# before trusting it, so this cannot rot back into a check that always succeeds.
crlf_probe="$(mktemp)"
printf 'probe\r\n' > "$crlf_probe"
if ! LC_ALL=C grep -qU $'\r' "$crlf_probe"; then
  rm -f "$crlf_probe"
  fail "CRLF detector is not working on this platform; the line-ending check cannot be trusted"
fi
rm -f "$crlf_probe"

while IFS= read -r -d '' file; do
  file="$ROOT_DIR/${file#$ROOT_DIR/}"
  [[ -f "$file" ]] || continue
  LC_ALL=C grep -Iq . "$file" 2>/dev/null || continue

  if LC_ALL=C grep -qU $'\r' "$file"; then
    fail "CRLF line ending found in ${file#$ROOT_DIR/}"
  fi

  if [[ -s "$file" && "$(tail -c 1 "$file" | wc -l)" -eq 0 ]]; then
    fail "missing final newline in ${file#$ROOT_DIR/}"
  fi
done < <(list_repo_files)
pass "line endings are LF"

pass "clean-code-skills repository is valid"
