#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT_DIR/templates/agent-block.md"
BEGIN_MARKER='<!-- clean-code-skills:begin'
END_MARKER='<!-- clean-code-skills:end -->'
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

[[ -f "$TEMPLATE" ]] || { printf 'ERROR: missing %s\n' "$TEMPLATE" >&2; exit 1; }
VERSION="$(sed -n "s/^<!-- clean-code-skills:begin v\(.*\) -->$/\1/p" "$TEMPLATE")"
[[ -n "$VERSION" ]] || { printf 'ERROR: could not read version from template begin marker\n' >&2; exit 1; }

if [[ "$GLOBAL" -eq 1 ]]; then
  TARGET_DIR="${CLEAN_CODE_HOME:-$HOME}"
fi

if [[ "$UNINSTALL" -eq 0 ]]; then
  mkdir -p "$TARGET_DIR"
fi
[[ -d "$TARGET_DIR" ]] || { printf 'ERROR: target %s does not exist\n' "$TARGET_DIR" >&2; exit 1; }
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

relpath() {
  printf '%s' "${1#"$TARGET_DIR"/}"
}

# --- detection ---------------------------------------------------------------

has_block() {
  [[ -f "$1" ]] && grep -q "$BEGIN_MARKER" "$1"
}

detect_profiles() {
  local found=()
  if [[ "$GLOBAL" -eq 1 ]]; then
    { has_block "$TARGET_DIR/.claude/CLAUDE.md" || [[ -d "$TARGET_DIR/.claude/skills/clean-code" ]]; } && found+=(claude)
    { has_block "$TARGET_DIR/.codex/AGENTS.md" || [[ -d "$TARGET_DIR/.agents/skills/clean-code" ]]; } && found+=(codex)
    has_block "$TARGET_DIR/.config/opencode/AGENTS.md" && found+=(opencode)
    has_block "$TARGET_DIR/.gemini/GEMINI.md" && found+=(gemini)
    [[ -d "$TARGET_DIR/.grok/skills/clean-code" ]] && found+=(grok)
    [[ -d "$TARGET_DIR/.gemini/config/skills/clean-code" ]] && found+=(antigravity)
  else
    { has_block "$TARGET_DIR/CLAUDE.md" || [[ -d "$TARGET_DIR/.claude/skills/clean-code" ]]; } && found+=(claude)
    { has_block "$TARGET_DIR/AGENTS.md" || [[ -d "$TARGET_DIR/.agents/skills/clean-code" ]]; } && found+=(agents)
    has_block "$TARGET_DIR/GEMINI.md" && found+=(gemini)
    [[ -f "$TARGET_DIR/.cursor/rules/clean-code.mdc" ]] && found+=(cursor)
    { has_block "$TARGET_DIR/.github/copilot-instructions.md" || [[ -d "$TARGET_DIR/.github/skills/clean-code" ]]; } && found+=(copilot)
    [[ -f "$TARGET_DIR/.windsurf/rules/clean-code.md" ]] && found+=(windsurf)
    [[ -f "$TARGET_DIR/.clinerules/clean-code.md" ]] && found+=(cline)
    [[ -d "$TARGET_DIR/.grok/skills/clean-code" ]] && found+=(grok)
    [[ -d "$TARGET_DIR/skills/clean-code" ]] && found+=(skill)
  fi
  printf '%s\n' "${found[@]:-}"
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

# --- managed block in shared files ---------------------------------------

merge_block() {
  local dest="$1"
  local begin_count end_count

  mkdir -p "$(dirname "$dest")"

  if [[ ! -e "$dest" ]]; then
    cat "$TEMPLATE" > "$dest"
    printf 'INSTALLED: %s (new file with managed block v%s)\n' "$(relpath "$dest")" "$VERSION"
    return
  fi

  begin_count="$(grep -c "$BEGIN_MARKER" "$dest" || true)"
  end_count="$(grep -cF "$END_MARKER" "$dest" || true)"

  if [[ "$begin_count" -eq 0 && "$end_count" -eq 0 ]]; then
    # Ensure the file ends with a newline, then append the block.
    if [[ -s "$dest" && "$(tail -c 1 "$dest" | wc -l)" -eq 0 ]]; then
      printf '\n' >> "$dest"
    fi
    printf '\n' >> "$dest"
    cat "$TEMPLATE" >> "$dest"
    printf 'UPDATED: %s (managed block v%s appended; existing content preserved)\n' "$(relpath "$dest")" "$VERSION"
    return
  fi

  if [[ "$begin_count" -ne 1 || "$end_count" -ne 1 ]]; then
    printf 'ERROR: %s has malformed clean-code-skills markers (begin=%s end=%s); fix manually\n' \
      "$(relpath "$dest")" "$begin_count" "$end_count" >&2
    exit 1
  fi

  local tmp
  tmp="$(mktemp)"
  awk -v tpl="$TEMPLATE" -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    index($0, begin) == 1 {
      while ((getline line < tpl) > 0) print line
      close(tpl)
      skipping = 1
      next
    }
    index($0, end) == 1 && skipping { skipping = 0; next }
    !skipping { print }
  ' "$dest" > "$tmp"
  mv "$tmp" "$dest"
  printf 'UPDATED: %s (managed block replaced with v%s)\n' "$(relpath "$dest")" "$VERSION"
}

remove_block() {
  local dest="$1"
  [[ -e "$dest" ]] || return 0
  if ! grep -q "$BEGIN_MARKER" "$dest"; then
    return 0
  fi

  local tmp
  tmp="$(mktemp)"
  awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    index($0, begin) == 1 { skipping = 1; next }
    index($0, end) == 1 && skipping { skipping = 0; next }
    !skipping { print }
  ' "$dest" > "$tmp"

  if [[ -z "$(tr -d '[:space:]' < "$tmp")" ]]; then
    rm -f "$tmp" "$dest"
    printf 'REMOVED: %s (file contained only the managed block)\n' "$(relpath "$dest")"
  else
    mv "$tmp" "$dest"
    printf 'UPDATED: %s (managed block removed; your content kept)\n' "$(relpath "$dest")"
  fi
}

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

skip_in_global() {
  printf 'SKIP: %s is project-scoped; run without --global for a specific project.\n' "$1"
}

# --- profiles --------------------------------------------------------------

apply_global_profile() {
  case "$1" in
    all)
      apply_global_profile claude
      apply_global_profile agents
      apply_global_profile gemini
      apply_global_profile grok
      apply_global_profile antigravity
      ;;
    claude)
      block_target "$TARGET_DIR/.claude/CLAUDE.md"
      skill_target "$TARGET_DIR/.claude/skills/clean-code"
      ;;
    agents)
      apply_global_profile codex
      apply_global_profile opencode
      skill_target "$TARGET_DIR/.agents/skills/clean-code"
      ;;
    codex)
      block_target "$TARGET_DIR/.codex/AGENTS.md"
      ;;
    opencode)
      block_target "$TARGET_DIR/.config/opencode/AGENTS.md"
      ;;
    jules)
      apply_global_profile agents
      ;;
    gemini)
      block_target "$TARGET_DIR/.gemini/GEMINI.md"
      ;;
    grok)
      skill_target "$TARGET_DIR/.grok/skills/clean-code"
      ;;
    antigravity)
      # Antigravity's personal skill root is the Gemini config dir, not ~/.agents/skills.
      skill_target "$TARGET_DIR/.gemini/config/skills/clean-code"
      ;;
    cursor|copilot|windsurf|cline|skill)
      skip_in_global "$1"
      ;;
    *)
      printf 'Unknown profile: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
}

apply_project_profile() {
  case "$1" in
    all)
      apply_project_profile claude
      apply_project_profile agents
      apply_project_profile gemini
      apply_project_profile cursor
      apply_project_profile copilot
      apply_project_profile windsurf
      apply_project_profile cline
      apply_project_profile grok
      apply_project_profile skill
      ;;
    claude)
      block_target "$TARGET_DIR/CLAUDE.md"
      skill_target "$TARGET_DIR/.claude/skills/clean-code"
      ;;
    agents|codex|opencode|jules)
      block_target "$TARGET_DIR/AGENTS.md"
      # .agents/skills is the shared cross-agent skill root: Codex CLI, GitHub Copilot,
      # Gemini CLI and Amp all read it, so installing here makes the skill itself
      # discoverable rather than only the instruction block.
      skill_target "$TARGET_DIR/.agents/skills/clean-code"
      ;;
    gemini)
      block_target "$TARGET_DIR/GEMINI.md"
      ;;
    cursor)
      owned_file_target "$ROOT_DIR/.cursor/rules/clean-code.mdc" "$TARGET_DIR/.cursor/rules/clean-code.mdc"
      ;;
    copilot)
      block_target "$TARGET_DIR/.github/copilot-instructions.md"
      owned_file_target "$ROOT_DIR/.github/instructions/clean-code.instructions.md" "$TARGET_DIR/.github/instructions/clean-code.instructions.md"
      skill_target "$TARGET_DIR/.github/skills/clean-code"
      ;;
    windsurf)
      owned_file_target "$ROOT_DIR/.windsurf/rules/clean-code.md" "$TARGET_DIR/.windsurf/rules/clean-code.md"
      ;;
    cline)
      owned_file_target "$ROOT_DIR/.clinerules/clean-code.md" "$TARGET_DIR/.clinerules/clean-code.md"
      ;;
    grok)
      # Grok Build CLI reads AGENTS.md, but its project skill root is .grok/skills,
      # not the shared .agents/skills root.
      block_target "$TARGET_DIR/AGENTS.md"
      skill_target "$TARGET_DIR/.grok/skills/clean-code"
      ;;
    antigravity)
      # Antigravity defaults to the shared project root; only its personal root differs.
      skill_target "$TARGET_DIR/.agents/skills/clean-code"
      ;;
    skill)
      skill_target "$TARGET_DIR/skills/clean-code"
      ;;
    *)
      printf 'Unknown profile: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
}

for profile in "${profiles[@]}"; do
  if [[ "$GLOBAL" -eq 1 ]]; then
    apply_global_profile "$profile"
  else
    apply_project_profile "$profile"
  fi
done

if [[ "$UNINSTALL" -eq 1 ]]; then
  printf 'Clean-code uninstall complete for %s\n' "$TARGET_DIR"
else
  printf 'Clean-code v%s install complete for %s\n' "$VERSION" "$TARGET_DIR"
  printf 'To update later: re-run with --detect (or use scripts/remote-install.sh | bash -s -- --detect).\n'
fi
