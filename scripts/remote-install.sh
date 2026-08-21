#!/usr/bin/env bash
# No-clone installer: downloads the latest clean-code-skills release (or main)
# and runs the packaged installer against the current directory.
#
#   curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- all
#   curl -fsSL .../remote-install.sh | bash -s -- claude cursor
#   curl -fsSL .../remote-install.sh | bash -s -- --detect        # update what is already installed
#   curl -fsSL .../remote-install.sh | bash -s -- --uninstall all
#
# Environment overrides:
#   CLEAN_CODE_REPO  owner/name (default btseee/clean-code-skills)
#   CLEAN_CODE_REF   tag or branch to install (default: latest release, else main)
set -euo pipefail

REPO="${CLEAN_CODE_REPO:-btseee/clean-code-skills}"
REF="${CLEAN_CODE_REF:-}"

command -v curl >/dev/null 2>&1 || { printf 'ERROR: curl is required\n' >&2; exit 1; }
command -v tar >/dev/null 2>&1 || { printf 'ERROR: tar is required\n' >&2; exit 1; }

if [[ -z "$REF" ]]; then
  REF="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1 || true)"
fi
[[ -n "$REF" ]] || REF="main"

tmp="$(mktemp -d)"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

printf 'Downloading clean-code-skills %s...\n' "$REF"
curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$REF" | tar -xz -C "$tmp" --strip-components=1

bash "$tmp/scripts/install.sh" --target "$(pwd)" "$@"
