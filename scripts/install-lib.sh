#!/usr/bin/env bash
# Shared by install.sh and sync.sh. Source it after setting ROOT_DIR.
# The host table (templates/hosts.tsv) is the only place a host path lives.

HOSTS="$ROOT_DIR/templates/hosts.tsv"
[[ -f "$HOSTS" ]] || { printf 'ERROR: missing %s\n' "$HOSTS" >&2; exit 1; }

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
