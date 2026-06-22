#!/usr/bin/env bash
set -u

workspace="${1:-.}"
source_file="${2:-}"

echo "== workspace =="
echo "path: $workspace"
if [ -d "$workspace" ]; then
  (cd "$workspace" && echo "pwd: $PWD" && echo "realpath: $(realpath .)")
fi

echo
echo "== clangd binary =="
command -v clangd || true
clangd --version 2>/dev/null | head -5 || true

echo
echo "== user config =="
user_cfg="${XDG_CONFIG_HOME:-$HOME/.config}/clangd/config.yaml"
if [ -f "$user_cfg" ]; then
  echo "[present] $user_cfg"
  sed -n '1,120p' "$user_cfg"
else
  echo "[missing] $user_cfg"
fi

echo
echo "== workspace config =="
for f in \
  "$workspace/.vscode/settings.json" \
  "$workspace/.clangd" \
  "$workspace/compile_commands.json"
do
  if [ -e "$f" ]; then
    echo "[present] $f"
    case "$f" in
      *.clangd|*/settings.json) sed -n '1,120p' "$f" ;;
      */compile_commands.json)
        ls -lh "$f"
        python3 - "$f" <<'PY' 2>/dev/null || true
import json, sys
with open(sys.argv[1]) as fh:
    data = json.load(fh)
print(f"entries: {len(data)}")
if data:
    print(f"sample directory: {data[0].get('directory')}")
    print(f"sample file: {data[0].get('file')}")
PY
        ;;
    esac
  else
    echo "[missing] $f"
  fi
done

echo
echo "== nearby compile databases =="
find "$workspace" -maxdepth 5 -name compile_commands.json -printf '%p\n' 2>/dev/null | sort | head -40

echo
echo "== clangd/cpptools processes =="
ps -ef | grep -E 'clangd|cpptools' | grep -v grep || true

echo
echo "== recent clangd log highlights =="
find "$HOME/.vscode-server/data/logs" -type f -name '*clangd*.log' 2>/dev/null \
  -printf '%T@ %p\n' | sort -nr | head -5 | cut -d' ' -f2- | while read -r log; do
    echo "-- $log --"
    grep -nE 'Working directory|Loaded compilation database|Failed to find compilation database|ASTWorker building file|command clangd fallback|command inferred from|Loading config file' "$log" | tail -30 || true
  done

if [ -n "$source_file" ]; then
  echo
  echo "== manual check =="
  clangd --check="$source_file" --log=info 2>&1 | grep -E 'Loaded compilation database|Failed to find compilation database|Compile command|All checks|errors' || true
fi
