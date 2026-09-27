#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  unlock-and-disable-gnome-idle.sh --host HOST [--ssh-user USER] [--session-user USER] [--port PORT]

Examples:
  unlock-and-disable-gnome-idle.sh --host 192.168.31.95 --ssh-user cat --session-user cat
  unlock-and-disable-gnome-idle.sh --host 192.168.31.95 --ssh-user root --session-user cat
EOF
}

host=""
ssh_user=""
session_user=""
port="22"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      host="${2:-}"
      shift 2
      ;;
    --ssh-user)
      ssh_user="${2:-}"
      shift 2
      ;;
    --session-user)
      session_user="${2:-}"
      shift 2
      ;;
    --port)
      port="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$host" ]]; then
  usage >&2
  exit 2
fi

if [[ -z "$ssh_user" && -n "$session_user" ]]; then
  ssh_user="$session_user"
fi

if [[ -z "$session_user" && -n "$ssh_user" ]]; then
  session_user="$ssh_user"
fi

if [[ -z "$ssh_user" || -z "$session_user" ]]; then
  echo "Both --ssh-user and --session-user must resolve to non-empty values." >&2
  exit 2
fi

target="${ssh_user}@${host}"

read -r -d '' remote_script <<'EOF' || true
set -euo pipefail

session_user="$1"

as_session_user() {
  if [[ "$(id -un)" == "$session_user" ]]; then
    "$@"
    return
  fi

  if [[ "$(id -u)" -eq 0 ]] && command -v runuser >/dev/null 2>&1; then
    runuser -u "$session_user" -- "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo -u "$session_user" "$@"
    return
  fi

  echo "Cannot switch to session user '$session_user'. Use same-user SSH or root SSH." >&2
  exit 1
}

find_graphical_session() {
  local sid type class active remote name
  while read -r sid _rest; do
    [[ -n "$sid" ]] || continue
    type="$(loginctl show-session "$sid" -p Type --value 2>/dev/null || true)"
    class="$(loginctl show-session "$sid" -p Class --value 2>/dev/null || true)"
    active="$(loginctl show-session "$sid" -p Active --value 2>/dev/null || true)"
    remote="$(loginctl show-session "$sid" -p Remote --value 2>/dev/null || true)"
    name="$(loginctl show-session "$sid" -p Name --value 2>/dev/null || true)"

    if [[ "$name" == "$session_user" && "$class" == "user" && "$remote" == "no" && ( "$type" == "x11" || "$type" == "wayland" ) ]]; then
      if [[ "$active" == "yes" ]]; then
        echo "$sid"
        return 0
      fi

      fallback_sid="$sid"
    fi
  done < <(loginctl list-sessions --no-legend 2>/dev/null || loginctl list-sessions 2>/dev/null)

  if [[ -n "${fallback_sid:-}" ]]; then
    echo "$fallback_sid"
    return 0
  fi

  return 1
}

find_env_pid() {
  local pid
  for pid in $(pgrep -u "$session_user" -f 'gnome-shell|plasmashell|xfce4-session|lxqt-session|cinnamon-session|mate-session|kwin_wayland|weston' 2>/dev/null || true); do
    if [[ -r "/proc/$pid/environ" ]]; then
      echo "$pid"
      return 0
    fi
  done

  for pid in $(pgrep -u "$session_user" . 2>/dev/null || true); do
    if [[ -r "/proc/$pid/environ" ]] && tr '\0' '\n' <"/proc/$pid/environ" | grep -q '^DISPLAY='; then
      echo "$pid"
      return 0
    fi
  done

  return 1
}

extract_env_value() {
  local pid="$1"
  local key="$2"
  tr '\0' '\n' <"/proc/$pid/environ" | sed -n "s/^${key}=//p" | head -n1
}

session_id="$(find_graphical_session || true)"
if [[ -z "$session_id" ]]; then
  echo "No local graphical session found for user '$session_user'." >&2
  loginctl list-sessions --no-legend || true
  exit 1
fi

uid="$(id -u "$session_user")"
leader_pid="$(loginctl show-session "$session_id" -p Leader --value 2>/dev/null || true)"
probe_pid="$(find_env_pid || true)"
probe_pid="${probe_pid:-$leader_pid}"

display=""
runtime_dir="/run/user/$uid"
dbus_addr=""

if [[ -n "$probe_pid" && -r "/proc/$probe_pid/environ" ]]; then
  display="$(extract_env_value "$probe_pid" DISPLAY || true)"
  runtime_dir="$(extract_env_value "$probe_pid" XDG_RUNTIME_DIR || true)"
  dbus_addr="$(extract_env_value "$probe_pid" DBUS_SESSION_BUS_ADDRESS || true)"
fi

display="${display:-:0}"
runtime_dir="${runtime_dir:-/run/user/$uid}"

echo "Target session: $session_id"
echo "Probe PID: ${probe_pid:-unknown}"
echo "DISPLAY=$display"
echo "XDG_RUNTIME_DIR=$runtime_dir"
if [[ -n "$dbus_addr" ]]; then
  echo "DBUS_SESSION_BUS_ADDRESS=$dbus_addr"
else
  echo "DBUS_SESSION_BUS_ADDRESS=<not found>"
fi

loginctl unlock-session "$session_id" || true

session_env=(env "DISPLAY=$display" "XDG_RUNTIME_DIR=$runtime_dir")
if [[ -n "$dbus_addr" ]]; then
  session_env+=("DBUS_SESSION_BUS_ADDRESS=$dbus_addr")
fi

if command -v gdbus >/dev/null 2>&1 && [[ -n "$dbus_addr" ]]; then
  as_session_user "${session_env[@]}" \
    gdbus call --session \
      --dest org.gnome.ScreenSaver \
      --object-path /org/gnome/ScreenSaver \
      --method org.gnome.ScreenSaver.SetActive false >/dev/null 2>&1 || true

  as_session_user "${session_env[@]}" \
    gdbus call --session \
      --dest org.freedesktop.ScreenSaver \
      --object-path /org/freedesktop/ScreenSaver \
      --method org.freedesktop.ScreenSaver.SetActive false >/dev/null 2>&1 || true
fi

if command -v gsettings >/dev/null 2>&1; then
  as_session_user "${session_env[@]}" gsettings set org.gnome.desktop.session idle-delay 0 || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.desktop.screensaver lock-enabled false || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.desktop.screensaver lock-delay 0 || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing' || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing' || true
  as_session_user "${session_env[@]}" gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0 || true
fi

echo "Verification:"
loginctl show-session "$session_id" -p LockedHint -p Active -p State
if command -v gdbus >/dev/null 2>&1 && [[ -n "$dbus_addr" ]]; then
  as_session_user "${session_env[@]}" \
    gdbus call --session \
      --dest org.gnome.ScreenSaver \
      --object-path /org/gnome/ScreenSaver \
      --method org.gnome.ScreenSaver.GetActive 2>/dev/null || true
fi

if command -v gsettings >/dev/null 2>&1; then
  as_session_user "${session_env[@]}" gsettings get org.gnome.desktop.session idle-delay || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.desktop.screensaver lock-enabled || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.desktop.screensaver lock-delay || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type || true
  as_session_user "${session_env[@]}" gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout || true
fi
EOF

ssh -o BatchMode=yes -o ConnectTimeout=8 -p "$port" "$target" \
  "bash -s -- $(printf '%q' "$session_user")" <<<"$remote_script"
