#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=install-lib.sh
source "$ROOT_DIR/scripts/install-lib.sh"
TARGET_DIR="$(pwd)"
FORCE=0
UNINSTALL=0
GLOBAL=0
DETECT=0
profiles=()

usage() {
  cat <<'USAGE'
Usage: bash scripts/install.sh [options] [profile...]

Installs, updates, or removes clean-code guidance. Shared files (CLAUDE.md,
AGENTS.md, GEMINI.md, .github/copilot-instructions.md) receive a managed block
between clean-code-skills markers; your own content in those files is
preserved, and re-running the installer updates only the block. Dedicated
files and skill folders are owned by this package and are replaced on every
run.

Profiles (project mode):
  all       Every target below
  claude    CLAUDE.md block + .claude/skills/clean-code/
  agents    AGENTS.md block + .agents/skills/clean-code/ (Codex CLI, opencode, Jules,
            Amp, and any host reading the shared .agents/skills root)
  codex     Alias for agents
  opencode  Alias for agents
  jules     Alias for agents
  gemini    GEMINI.md block
  cursor    .cursor/rules/clean-code.mdc
  copilot   .github/copilot-instructions.md block + instructions file + .github/skills/clean-code/
  windsurf  .windsurf/rules/clean-code.md
  cline     .clinerules/clean-code.md
  grok      AGENTS.md block + .grok/skills/clean-code/ (Grok Build CLI)
  antigravity  .agents/skills/clean-code/ (same shared root as agents)
  skill     skills/clean-code/ (portable copy for any skill-aware harness)

Profiles (--global mode, installed once for all projects in your home directory):
  claude    ~/.claude/CLAUDE.md block + ~/.claude/skills/clean-code/
  codex     ~/.codex/AGENTS.md block
  opencode  ~/.config/opencode/AGENTS.md block
  gemini    ~/.gemini/GEMINI.md block
  agents    codex + opencode + ~/.agents/skills/clean-code/
  grok      ~/.grok/skills/clean-code/
  antigravity  ~/.gemini/config/skills/clean-code/
  all       claude + agents + gemini + grok + antigravity
  (cursor, copilot, windsurf, cline, and skill are project-scoped and are skipped globally)

Options:
  --target DIR   Project to install into (default: current directory)
  --global       Install into your home directory for all projects instead of one project
  --detect       Operate on the profiles already present in the target (for updates)
  --force        Overwrite dedicated files that exist but were not created by this package
  --uninstall    Remove managed blocks and package-owned files for the given profiles
  -h, --help     Show this help

Examples:
  bash scripts/install.sh --target ../my-project all
  bash scripts/install.sh --target ../my-project claude cursor copilot
  bash scripts/install.sh --target ../my-project --detect          # update what is installed
  bash scripts/install.sh --global claude codex gemini
  bash scripts/install.sh --target ../my-project --uninstall all

Update: pull the latest clean-code-skills (or use scripts/remote-install.sh),
then re-run the same command; --detect re-installs exactly what is present.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { usage >&2; exit 1; }
      TARGET_DIR="$2"
      shift 2
      ;;
    --global)
      GLOBAL=1
      shift
      ;;
    --detect)
      DETECT=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      printf 'Unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
    *)
      profiles+=("$1")
      shift
      ;;
  esac
done

VERSION="$(template_version)"

if [[ "$GLOBAL" -eq 1 ]]; then
  TARGET_DIR="${CLEAN_CODE_HOME:-$HOME}"
fi

if [[ "$UNINSTALL" -eq 0 ]]; then
  mkdir -p "$TARGET_DIR"
fi
[[ -d "$TARGET_DIR" ]] || { printf 'ERROR: target %s does not exist\n' "$TARGET_DIR" >&2; exit 1; }
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# --- detection ---------------------------------------------------------------

scope() {
  if [[ "$GLOBAL" -eq 1 ]]; then printf 'global'; else printf 'project'; fi
}

# A profile is installed when any of its detect-flagged paths is present:
# a shared file carrying the block, an owned file, or a skill folder.
detect_profiles() {
  local profile kind path
  while IFS=$'\t' read -r profile kind path; do
    case "$kind" in
      block) has_block "$TARGET_DIR/$path" && printf '%s\n' "$profile" ;;
      owned) [[ -f "$TARGET_DIR/$path" ]] && printf '%s\n' "$profile" ;;
      skill) [[ -d "$TARGET_DIR/$path" ]] && printf '%s\n' "$profile" ;;
    esac
  done < <(host_detect "$(scope)") | awk '!seen[$0]++'
}

if [[ "$DETECT" -eq 1 ]]; then
  while IFS= read -r detected; do
    [[ -n "$detected" ]] && profiles+=("$detected")
  done < <(detect_profiles)
  if [[ ${#profiles[@]} -eq 0 ]]; then
    printf 'Nothing to detect in %s. Run again with explicit profiles (for example: all).\n' "$TARGET_DIR" >&2
    exit 1
  fi
  printf 'Detected profiles: %s\n' "${profiles[*]}"
fi

if [[ ${#profiles[@]} -eq 0 ]]; then
  profiles=(all)
fi

block_target() {
  if [[ "$UNINSTALL" -eq 1 ]]; then
    remove_block "$1"
  else
    merge_block "$1"
  fi
}

# --- dedicated files and skill folders ------------------------------------

copy_owned_file() {
  local source_file="$1"
  local dest_file="$2"

  if [[ -e "$dest_file" ]] && ! grep -q 'clean-code' "$dest_file" && [[ "$FORCE" -ne 1 ]]; then
    printf 'SKIP: %s exists and was not created by this package. Use --force to overwrite.\n' "$(relpath "$dest_file")"
    return
  fi

  mkdir -p "$(dirname "$dest_file")"
  if [[ -e "$dest_file" ]]; then
    cp "$source_file" "$dest_file"
    printf 'UPDATED: %s (v%s)\n' "$(relpath "$dest_file")" "$VERSION"
  else
    cp "$source_file" "$dest_file"
    printf 'INSTALLED: %s (v%s)\n' "$(relpath "$dest_file")" "$VERSION"
  fi
}

remove_owned_file() {
  local dest_file="$1"
  [[ -e "$dest_file" ]] || return 0
  rm -f "$dest_file"
  printf 'REMOVED: %s\n' "$(relpath "$dest_file")"
  rmdir -p "$(dirname "$dest_file")" 2>/dev/null || true
}

copy_skill_dir() {
  local dest_dir="$1"
  local verb="INSTALLED"
  [[ -e "$dest_dir" ]] && verb="UPDATED"
  rm -rf "$dest_dir"
  mkdir -p "$(dirname "$dest_dir")"
  cp -R "$ROOT_DIR/skills/clean-code" "$dest_dir"
  # A checkout that has run the scripts holds bytecode caches that embed its own paths.
  find "$dest_dir" \( -name '__pycache__' -o -name '*.pyc' \) -prune -exec rm -rf {} +
  printf '%s: %s/ (v%s)\n' "$verb" "$(relpath "$dest_dir")" "$VERSION"
}

remove_skill_dir() {
  local dest_dir="$1"
  [[ -e "$dest_dir" ]] || return 0
  rm -rf "$dest_dir"
  printf 'REMOVED: %s/\n' "$(relpath "$dest_dir")"
  rmdir -p "$(dirname "$dest_dir")" 2>/dev/null || true
}

skill_target() {
  if [[ "$UNINSTALL" -eq 1 ]]; then
    remove_skill_dir "$1"
  else
    copy_skill_dir "$1"
  fi
}

owned_file_target() {
  if [[ "$UNINSTALL" -eq 1 ]]; then
    remove_owned_file "$2"
  else
    copy_owned_file "$1" "$2"
  fi
}

# --- profiles --------------------------------------------------------------

apply_profile() {
  local profile="$1" rows kind path _
  rows="$(host_rows "$(scope)" "$profile")"
  if [[ -z "$rows" ]]; then
    if [[ -n "$(host_rows project "$profile")$(host_rows global "$profile")" ]]; then
      printf 'SKIP: %s is project-scoped; run without --global for a specific project.\n' "$profile"
      return
    fi
    printf 'Unknown profile: %s\n\n' "$profile" >&2
    usage >&2
    exit 1
  fi
  while IFS=$'\t' read -r kind path _; do
    case "$kind" in
      include) apply_profile "$path" ;;
      block) block_target "$TARGET_DIR/$path" ;;
      owned) owned_file_target "$ROOT_DIR/$path" "$TARGET_DIR/$path" ;;
      skill) skill_target "$TARGET_DIR/$path" ;;
      *) printf 'ERROR: unknown kind %s in %s\n' "$kind" "$HOSTS" >&2; exit 1 ;;
    esac
  done <<< "$rows"
}

for profile in "${profiles[@]}"; do
  apply_profile "$profile"
done

if [[ "$UNINSTALL" -eq 1 ]]; then
  printf 'Clean-code uninstall complete for %s\n' "$TARGET_DIR"
else
  printf 'Clean-code v%s install complete for %s\n' "$VERSION" "$TARGET_DIR"
  printf 'To update later: re-run with --detect (or use scripts/remote-install.sh | bash -s -- --detect).\n'
fi
