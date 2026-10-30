#!/usr/bin/env bash
set -u

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <workspace> [source-file]" >&2
  exit 2
fi

workspace=$1
source_file=${2:-}

echo "== workspace =="
printf 'input: %s\n' "$workspace"
if [[ -d "$workspace" ]]; then
  printf 'realpath: %s\n' "$(realpath "$workspace")"
else
  echo "workspace does not exist"
fi

echo
echo "== clangd =="
command -v clangd || true
clangd --version 2>/dev/null | head -5 || true

echo
echo "== user config =="
user_config="${XDG_CONFIG_HOME:-$HOME/.config}/clangd/config.yaml"
if [[ -f "$user_config" ]]; then
  printf '[present] %s\n' "$user_config"
  sed -n '1,160p' "$user_config"
else
  printf '[missing] %s\n' "$user_config"
fi

echo
echo "== workspace config =="
for path in \
  "$workspace/.vscode/settings.json" \
  "$workspace/.clangd" \
  "$workspace/compile_commands.json"
do
  if [[ -e "$path" ]]; then
    printf '[present] %s\n' "$path"
    case "$path" in
      */settings.json|*/.clangd) sed -n '1,180p' "$path" ;;
      */compile_commands.json)
        ls -lh "$path"
        python3 - "$path" <<'PY' 2>/dev/null || true
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
print(f"entries: {len(data)}")
if data:
    print(f"sample directory: {data[0].get('directory')}")
    print(f"sample file: {data[0].get('file')}")
PY
        ;;
    esac
  else
    printf '[missing] %s\n' "$path"
  fi
done

echo
echo "== nearby databases =="
find "$workspace" -maxdepth 5 -name compile_commands.json -type f -print 2>/dev/null \
  | sort | head -50

echo
echo "== clangd and competing processes =="
ps -u "$(id -u)" -o pid=,cwd=,args= 2>/dev/null \
  | grep -E 'clangd|cpptools' | grep -v grep || true

echo
echo "== recent VS Code clangd logs =="
find "$HOME/.vscode" "$HOME/.vscode-server" -type f -name '*clangd*.log' \
  -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -5 | cut -d' ' -f2- \
  | while read -r log; do
      [[ -n "$log" ]] || continue
      printf '%s\n' "-- $log --"
      if command -v rg >/dev/null; then
        rg -n 'Working directory:|Loading config file|Loaded compilation database|Failed to find compilation database|Compile command from CDB|command clangd fallback|command inferred from|ASTWorker building file' "$log" | tail -40 || true
      else
        grep -nE 'Working directory:|Loading config file|Loaded compilation database|Failed to find compilation database|Compile command from CDB|command clangd fallback|command inferred from|ASTWorker building file' "$log" | tail -40 || true
      fi
    done

if [[ -n "$source_file" ]]; then
  echo
  echo "== manual clangd check highlights =="
  clangd --check="$(realpath "$source_file")" \
    --compile-commands-dir="$(realpath "$workspace")" --log=info 2>&1 \
    | grep -E 'Loaded compilation database|Failed to find compilation database|Compile command|All checks|errors' || true
fi
