#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  repair_vscode_codex_remote.sh check --user USER
  repair_vscode_codex_remote.sh fix-server --user USER --commit COMMIT
  repair_vscode_codex_remote.sh copy-codex-extension --user USER --source-user SOURCE_USER [--version VERSION]

Notes:
  Run with sudo when USER is not the current user.
  The script moves broken VS Code Server installs aside; it does not delete user data.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

need_user_home() {
  local user="$1"
  getent passwd "$user" | cut -d: -f6
}

owner_group() {
  local user="$1"
  local group
  group="$(id -gn "$user")"
  printf '%s:%s' "$user" "$group"
}

require_user() {
  local user="$1"
  id "$user" >/dev/null 2>&1 || die "user not found: $user"
}

latest_openai_extension() {
  local home="$1"
  find "$home/.vscode-server/extensions" -maxdepth 1 -type d -name 'openai.chatgpt-*-linux-x64' 2>/dev/null \
    | sort -V \
    | tail -1
}

cmd="${1:-}"
if [ "$cmd" = "-h" ] || [ "$cmd" = "--help" ]; then
  usage
  exit 0
fi
shift || true

user=""
source_user=""
commit=""
version=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --user)
      user="${2:-}"
      shift 2
      ;;
    --source-user)
      source_user="${2:-}"
      shift 2
      ;;
    --commit)
      commit="${2:-}"
      shift 2
      ;;
    --version)
      version="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[ -n "$cmd" ] || { usage; exit 1; }
[ -n "$user" ] || die "--user is required"
require_user "$user"
home="$(need_user_home "$user")"
[ -n "$home" ] && [ -d "$home" ] || die "home directory not found for $user"

case "$cmd" in
  check)
    echo "== identity =="
    id "$user"
    getent passwd "$user"

    echo
    echo "== ownership =="
    for path in "$home" "$home/.vscode-server" "$home/.vscode-server/cli" "$home/.vscode-server/extensions" "$home/.codex"; do
      [ -e "$path" ] && stat -c '%U:%G %u:%g %a %n' "$path" || true
    done

    echo
    echo "== vscode processes =="
    ps -u "$user" -o pid,ppid,stat,etime,cmd --forest | sed -n '1,120p'

    echo
    echo "== server installs =="
    find "$home/.vscode-server/cli/servers" -maxdepth 2 -type d -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort | tail -40 || true

    echo
    echo "== recent logs =="
    find "$home/.vscode-server" -maxdepth 5 -type f -name '*.log' -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort | tail -40 || true

    echo
    echo "== openai extensions =="
    find "$home/.vscode-server/extensions" -maxdepth 1 -type d -name 'openai.chatgpt-*' -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort || true
    ;;

  fix-server)
    [ -n "$commit" ] || die "--commit is required for fix-server"
    stamp="$(date +%Y%m%d-%H%M%S)"
    base="$home/.vscode-server"
    srv="$base/cli/servers/Stable-$commit"
    bin="$base/code-$commit"
    owner="$(owner_group "$user")"

    echo "== stopping stuck VS Code Remote processes for $user =="
    pids="$(pgrep -u "$user" -f "vscode-server|code-$commit|command-shell|agent host" || true)"
    if [ -n "$pids" ]; then
      kill $pids || true
      sleep 1
      pids2="$(pgrep -u "$user" -f "vscode-server|code-$commit|command-shell|agent host" || true)"
      [ -n "$pids2" ] && kill -9 $pids2 || true
    fi

    echo "== stopping orphaned Remote SSH bootstrap sh/sleep leftovers =="
    ps -u "$user" -o pid=,cmd= \
      | awk '/^ *[0-9]+ sh$/ || /sleep 180/ {print $1}' \
      | xargs -r kill || true

    echo "== moving broken install aside =="
    [ -e "$srv" ] && mv "$srv" "$srv.broken-$stamp" && echo "$srv.broken-$stamp"
    [ -e "$bin" ] && mv "$bin" "$bin.broken-$stamp" && echo "$bin.broken-$stamp"

    find "$base" -maxdepth 1 -type d -name '_backup_cleanup_*' -print0 2>/dev/null \
      | while IFS= read -r -d '' cleanup; do
          mv "$cleanup" "$cleanup.broken-$stamp"
          echo "$cleanup.broken-$stamp"
        done

    echo "== repairing ownership =="
    [ -d "$base" ] && chown -R "$owner" "$base"
    [ -d "$home/.codex" ] && chown -R "$owner" "$home/.codex"
    [ -d "$base" ] && find "$base" -type d -exec chmod u+rwx {} +
    [ -d "$home/.codex" ] && find "$home/.codex" -type d -exec chmod u+rwx {} +

    echo "== remaining processes =="
    ps -u "$user" -o pid,ppid,stat,etime,cmd --forest | sed -n '1,80p'
    ;;

  copy-codex-extension)
    [ -n "$source_user" ] || die "--source-user is required for copy-codex-extension"
    require_user "$source_user"
    source_home="$(need_user_home "$source_user")"
    [ -d "$source_home" ] || die "home directory not found for $source_user"
    owner="$(owner_group "$user")"

    if [ -n "$version" ]; then
      src="$source_home/.vscode-server/extensions/openai.chatgpt-$version-linux-x64"
    else
      src="$(latest_openai_extension "$source_home")"
    fi
    [ -n "${src:-}" ] && [ -d "$src" ] || die "source OpenAI extension not found"

    dst="$home/.vscode-server/extensions/$(basename "$src")"
    mkdir -p "$home/.vscode-server/extensions"
    if [ ! -d "$dst" ]; then
      cp -a "$src" "$dst"
    fi
    chown -R "$owner" "$dst"
    chmod -R u+rwX "$dst"

    echo "copied: $src -> $dst"
    if [ -x "$dst/bin/linux-x86_64/codex" ]; then
      sudo -u "$user" "$dst/bin/linux-x86_64/codex" --version || true
    fi
    ;;

  *)
    usage
    exit 1
    ;;
esac
