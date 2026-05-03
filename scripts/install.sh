#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$(pwd)"
FORCE=0
profiles=()

usage() {
  cat <<'USAGE'
Usage: bash scripts/install.sh [--target DIR] [--force] [profile...]

Profiles:
  all       Install every supported instruction target
  claude    Install CLAUDE.md
  gemini    Install GEMINI.md
  agents    Install AGENTS.md
  cursor    Install .cursor/rules/clean-code.mdc
  copilot   Install GitHub Copilot instruction files
  skill     Install the skill to skills/clean-code and .github/skills/clean-code

Examples:
  bash scripts/install.sh --target ../my-project all
  bash scripts/install.sh --target ../my-project claude cursor copilot
  bash scripts/install.sh --target ../my-project --force all
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { usage >&2; exit 1; }
      TARGET_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      profiles+=("$1")
      shift
      ;;
  esac
done

if [[ ${#profiles[@]} -eq 0 ]]; then
  profiles=(all)
fi

mkdir -p "$TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

copy_file() {
  local source_file="$1"
  local dest_file="$2"

  mkdir -p "$(dirname "$dest_file")"

  if [[ -e "$dest_file" && "$(readlink -f "$source_file")" == "$(readlink -f "$dest_file")" ]]; then
    printf 'SKIP: %s is already the source file.\n' "${dest_file#$TARGET_DIR/}"
    return
  fi

  if [[ -e "$dest_file" && "$FORCE" -ne 1 ]]; then
    printf 'SKIP: %s exists. Use --force to overwrite.\n' "${dest_file#$TARGET_DIR/}"
    return
  fi

  cp "$source_file" "$dest_file"
  printf 'INSTALLED: %s\n' "${dest_file#$TARGET_DIR/}"
}

copy_dir() {
  local source_dir="$1"
  local dest_dir="$2"

  if [[ -e "$dest_dir" && "$(readlink -f "$source_dir")" == "$(readlink -f "$dest_dir")" ]]; then
    printf 'SKIP: %s is already the source directory.\n' "${dest_dir#$TARGET_DIR/}"
    return
  fi

  if [[ -e "$dest_dir" && "$FORCE" -ne 1 ]]; then
    printf 'SKIP: %s exists. Use --force to overwrite.\n' "${dest_dir#$TARGET_DIR/}"
    return
  fi

  rm -rf "$dest_dir"
  mkdir -p "$(dirname "$dest_dir")"
  cp -R "$source_dir" "$dest_dir"
  printf 'INSTALLED: %s\n' "${dest_dir#$TARGET_DIR/}"
}

install_profile() {
  case "$1" in
    all)
      install_profile claude
      install_profile gemini
      install_profile agents
      install_profile cursor
      install_profile copilot
      install_profile skill
      ;;
    claude)
      copy_file "$ROOT_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"
      ;;
    gemini)
      copy_file "$ROOT_DIR/GEMINI.md" "$TARGET_DIR/GEMINI.md"
      ;;
    agents)
      copy_file "$ROOT_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"
      ;;
    cursor)
      copy_file "$ROOT_DIR/.cursor/rules/clean-code.mdc" "$TARGET_DIR/.cursor/rules/clean-code.mdc"
      ;;
    copilot)
      copy_file "$ROOT_DIR/.github/copilot-instructions.md" "$TARGET_DIR/.github/copilot-instructions.md"
      copy_file "$ROOT_DIR/.github/instructions/clean-code.instructions.md" "$TARGET_DIR/.github/instructions/clean-code.instructions.md"
      ;;
    skill)
      copy_dir "$ROOT_DIR/skills/clean-code" "$TARGET_DIR/skills/clean-code"
      copy_dir "$ROOT_DIR/skills/clean-code" "$TARGET_DIR/.github/skills/clean-code"
      ;;
    *)
      printf 'Unknown profile: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
}

for profile in "${profiles[@]}"; do
  install_profile "$profile"
done

printf 'Clean-code installation complete for %s\n' "$TARGET_DIR"
