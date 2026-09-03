#!/usr/bin/env bash
# Proves each eval fixture still contains the flaw its scenario plants, using the bundled
# scripts where a flaw is machine-detectable. This does not grade an agent; it keeps the
# fixtures honest so that a later grade means something.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="$ROOT_DIR/skills/clean-code/scripts"
SCENARIOS="$ROOT_DIR/evals/scenarios"

if command -v python3 >/dev/null 2>&1; then PYTHON=python3; else PYTHON=python; fi

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$1"; }

for scenario in "$SCENARIOS"/*/; do
  name="$(basename "$scenario")"
  [[ -f "$scenario/TASK.md" ]] || fail "$name has no TASK.md"
  [[ -f "$ROOT_DIR/evals/expected/$name.md" ]] || fail "$name has no expected/$name.md"
done
pass "every scenario has a task and an expected outcome"

# boundary-violation: the domain imports infra, so the check must fail before the fix.
code=0; "$PYTHON" "$SCRIPTS/check_boundaries.py" --root "$SCENARIOS/boundary-violation" >/dev/null || code=$?
[[ "$code" -eq 1 ]] || fail "boundary-violation should exit 1 before the fix, got $code"
pass "boundary-violation fixture violates its declared layering"

# wrong-placement: clean before the task, so a misplaced rule is detectable afterwards.
"$PYTHON" "$SCRIPTS/check_boundaries.py" --root "$SCENARIOS/wrong-placement" >/dev/null \
  || fail "wrong-placement fixture should start with no violations"
pass "wrong-placement fixture starts clean"

# duplicate-logic: the sibling variant must be visible to scan_repo.
"$PYTHON" "$SCRIPTS/scan_repo.py" --root "$SCENARIOS/duplicate-logic" --json \
  | "$PYTHON" -c 'import json,sys; f=json.load(sys.stdin); assert f["sibling_variants"], "no sibling variant found"' \
  || fail "duplicate-logic fixture should contain a sibling variant"
pass "duplicate-logic fixture contains a sibling variant"

# unverified-success: the test command must actually fail here.
if command -v node >/dev/null 2>&1; then
  if node "$SCENARIOS/unverified-success/scripts/fail.js" >/dev/null 2>&1; then
    fail "unverified-success test command should fail"
  fi
  pass "unverified-success test command fails as planted"
else
  printf 'WARN: node not found; skipped the unverified-success command check\n'
fi

# every fixture is readable by the report card
for scenario in "$SCENARIOS"/*/; do
  "$PYTHON" "$SCRIPTS/architecture_report.py" --root "$scenario" --json >/dev/null \
    || fail "architecture_report failed on $(basename "$scenario")"
done
pass "architecture_report runs on every fixture"

pass "eval fixtures are intact"
