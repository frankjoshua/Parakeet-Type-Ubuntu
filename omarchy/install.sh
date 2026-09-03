#!/bin/bash
# Install Parakeet Dictation on Omarchy (Arch + Hyprland).
# Run from the repo checkout:  ./omarchy/install.sh
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HOME/.local/bin/parakeet-dictation"

sudo pacman -S --needed --noconfirm libc++ wtype wl-clipboard \
    libayatana-appindicator python-gobject portaudio libcanberra

# venv sees the system PyGObject; pip installs the rest
[ -d "$DIR/.venv" ] || python3 -m venv --system-site-packages "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt" requests tqdm

mkdir -p "$(dirname "$BIN")"
printf '#!/bin/bash\nexec "%s/.venv/bin/python" -u "%s/dictation_app.py" "$@"\n' "$DIR" "$DIR" > "$BIN"
chmod +x "$BIN"

# Hyprland: hotkeys + autostart (idempotent)
HYPR="$HOME/.config/hypr"
grep -q parakeet-dictation "$HYPR/bindings.lua" 2>/dev/null || cat >> "$HYPR/bindings.lua" <<EOF

-- Parakeet Dictation
o.bind("CTRL + 0", "Toggle dictation", "$BIN --toggle")
o.bind("CTRL + ALT + 0", "Pause dictation", "$BIN --pause")
EOF
grep -q parakeet-dictation "$HYPR/autostart.lua" 2>/dev/null || \
    echo "o.launch_on_start(\"$BIN\")" >> "$HYPR/autostart.lua"
hyprctl reload >/dev/null 2>&1 || true

echo "Installed. Start now with: $BIN &   (then download a model from the tray > Settings > Models)"
