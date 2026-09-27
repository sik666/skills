#!/usr/bin/env bash
set -euo pipefail

stamp=$(date +%Y%m%d_%H%M%S)
cache_dir="$HOME/.cache/clangd"

if [[ -d "$cache_dir" ]]; then
  backup="${cache_dir}.bak_${stamp}"
  mv "$cache_dir" "$backup"
  printf 'moved cache to %s\n' "$backup"
else
  echo "no global clangd cache"
fi

pids=$(pgrep -u "$(id -un)" -f '/clangd(_[0-9.]+)?/bin/clangd|/bin/clangd' || true)
if [[ -n "$pids" ]]; then
  printf 'killing clangd pids: %s\n' "$pids"
  kill $pids || true
else
  echo "no clangd process"
fi
