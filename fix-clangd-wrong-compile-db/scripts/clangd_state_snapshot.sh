#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <workspace> [source-file]" >&2
  exit 1
fi

workspace=$1
source_file=${2:-}

echo "== workspace =="
printf 'pwd: %s\n' "$(cd "$workspace" && pwd)"
printf 'realpath: %s\n' "$(realpath "$workspace")"

echo
echo "== local config =="
for path in \
  "$workspace/.vscode/settings.json" \
  "$workspace/.clangd" \
  "$workspace/compile_commands.json"
do
  if [[ -e "$path" ]]; then
    printf '[present] %s\n' "$path"
  else
    printf '[missing] %s\n' "$path"
  fi
done

echo
echo "== clangd processes =="
if pgrep -u "$(id -un)" -f clangd >/dev/null; then
  while read -r pid; do
    [[ -n "$pid" ]] || continue
    [[ -r "/proc/$pid/cmdline" ]] || continue
    printf 'pid=%s cwd=%s\n' "$pid" "$(readlink -f "/proc/$pid/cwd" 2>/dev/null || echo '?')"
    printf 'cmd=%s\n' "$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  done < <(pgrep -u "$(id -un)" -f clangd)
else
  echo "no clangd process"
fi

echo
echo "== recent clangd logs =="
find "$HOME/.vscode-server/data/logs" -path '*clangd.log' -type f -printf '%T@ %p\n' 2>/dev/null \
  | sort -nr | head -3 | cut -d' ' -f2- | while read -r log; do
    [[ -n "$log" ]] || continue
    printf '%s\n' "-- $log --"
    rg -n "Working directory:|Loading config file|Loaded compilation database|ASTWorker building file|command inferred from" "$log" || true
  done

if [[ -n "$source_file" ]]; then
  echo
  echo "== manual clangd check =="
  clangd --check="$source_file" --log=verbose 2>&1 \
    | rg "Testing on source file|Loading config file|Loaded compilation database|Compile command from CDB|All checks completed" || true
fi
