#!/usr/bin/env bash
# Shared by install.sh and sync.sh. Source it after setting ROOT_DIR; set TARGET_DIR
# before calling merge_block or remove_block.
#
# Two facts live here and nowhere else: the host table (templates/hosts.tsv) is the
# only place a host path lives, and the managed block is delimited by a begin marker
# that carries the version and a fixed end marker, at most one block per file.

HOSTS="$ROOT_DIR/templates/hosts.tsv"
TEMPLATE="$ROOT_DIR/templates/agent-block.md"
BEGIN_MARKER='<!-- clean-code-skills:begin'
END_MARKER='<!-- clean-code-skills:end -->'
[[ -f "$HOSTS" ]] || { printf 'ERROR: missing %s\n' "$HOSTS" >&2; exit 1; }
[[ -f "$TEMPLATE" ]] || { printf 'ERROR: missing %s\n' "$TEMPLATE" >&2; exit 1; }

# --- host table --------------------------------------------------------------

# host_rows SCOPE PROFILE -> lines of "kind<TAB>path<TAB>detect" for that profile.
host_rows() {
  awk -F'\t' -v scope="$1" -v profile="$2" \
    '!/^#/ && NF >= 4 && $1 == scope && $2 == profile { print $3 "\t" $4 "\t" $5 }' "$HOSTS"
}

# host_paths SCOPE KIND... -> unique paths of those kinds in that scope, in table order.
host_paths() {
  local scope="$1"; shift
  local kinds=" $* "
  awk -F'\t' -v scope="$scope" -v kinds="$kinds" \
    '!/^#/ && NF >= 4 && $1 == scope && index(kinds, " " $3 " ") && !seen[$4]++ { print $4 }' "$HOSTS"
}

# host_detect SCOPE -> lines of "profile<TAB>kind<TAB>path" for rows that signal presence.
host_detect() {
  awk -F'\t' -v scope="$1" \
    '!/^#/ && NF >= 5 && $1 == scope && $5 == "1" { print $2 "\t" $3 "\t" $4 }' "$HOSTS"
}

# --- managed block -----------------------------------------------------------

template_version() {
  local version
  version="$(sed -n "s/^${BEGIN_MARKER} v\(.*\) -->$/\1/p" "$TEMPLATE")"
  [[ -n "$version" ]] || { printf 'ERROR: could not read version from template begin marker\n' >&2; exit 1; }
  printf '%s' "$version"
}

relpath() {
  printf '%s' "${1#"$TARGET_DIR"/}"
}

has_block() {
  [[ -f "$1" ]] && grep -q "$BEGIN_MARKER" "$1"
}

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
    # merge_block inserts a blank separator line before an appended block. Removing the
    # block must take that separator with it, or install-then-uninstall leaves the file
    # one blank line longer each round trip instead of restoring it exactly.
    trimmed="$(mktemp)"
    awk '{ lines[NR] = $0 } END {
      last = NR
      while (last > 0 && lines[last] ~ /^[[:space:]]*$/) last--
      for (i = 1; i <= last; i++) print lines[i]
    }' "$tmp" > "$trimmed"
    mv "$trimmed" "$dest"
    rm -f "$tmp"
    printf 'UPDATED: %s (managed block removed; your content kept)\n' "$(relpath "$dest")"
  fi
}

