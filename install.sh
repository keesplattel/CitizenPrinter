#!/usr/bin/env bash
# Installs https://github.com/dandriscoll/receiptprinter on a Raspberry Pi as a
# systemd service. Run as your normal user (not root); it uses sudo where needed.
# Safe to re-run: it updates the checkout and restarts the service.
set -euo pipefail

REPO_URL="https://github.com/dandriscoll/receiptprinter"
APP_DIR="$HOME/receiptprinter"
PORT="${PORT:-4180}"
RUN_USER="$(id -un)"

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as your normal user, not root (it calls sudo itself)." >&2
  exit 1
fi

# --- Node.js >= 20 --------------------------------------------------------
node_major() { node -p 'process.versions.node.split(".")[0]'; }

log "Installing system packages"
sudo apt-get update -qq
sudo apt-get install -y -qq git ca-certificates curl usbutils

if ! command -v node >/dev/null || [ "$(node_major)" -lt 20 ]; then
  if [ "$(uname -m)" = "armv6l" ]; then
    echo "This is an armv6 Pi (Zero/1); NodeSource has no Node 20+ builds for it." >&2
    echo "Install Node 20+ manually (e.g. from unofficial-builds.nodejs.org) and re-run." >&2
    exit 1
  fi
  log "Installing Node.js 22 (NodeSource)"
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y -qq nodejs
fi
log "Node $(node -v), npm $(npm -v)"

# --- App ---------------------------------------------------------------------
if [ -d "$APP_DIR/.git" ]; then
  log "Updating $APP_DIR"
  git -C "$APP_DIR" pull --ff-only
else
  log "Cloning into $APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

log "Building (this can take a few minutes on a Pi)"
cd "$APP_DIR"
npm ci --no-audit --no-fund
npm run build
npm prune --omit=dev --no-audit --no-fund

# --- Printer device ----------------------------------------------------------
# Citizen printers show up either as a USB printer (/dev/usb/lp0) or, in their
# "virtual COM" USB mode, as a serial device (/dev/ttyACM0).
log "Looking for the printer"
lsusb | grep -i -E 'citizen|printer|epson' || warn "No obvious printer in lsusb output (is it plugged in and on?)"

PRINTER_DEVICE=""
for dev in /dev/usb/lp0 /dev/usb/lp1 /dev/ttyACM0 /dev/ttyUSB0; do
  if [ -e "$dev" ]; then PRINTER_DEVICE="$dev"; break; fi
done
if [ -z "$PRINTER_DEVICE" ]; then
  PRINTER_DEVICE=/dev/usb/lp0
  warn "No printer device found; defaulting to $PRINTER_DEVICE. Plug the printer in and run: sudo systemctl restart receiptprinter"
else
  echo "Using $PRINTER_DEVICE"
fi

EXEC_PRE=""
if [[ "$PRINTER_DEVICE" == /dev/tty* ]]; then
  # Raw mode on every start so the serial driver doesn't mangle ESC/POS bytes.
  EXEC_PRE="ExecStartPre=-/bin/stty -F $PRINTER_DEVICE raw -echo 115200"
fi

# Let the user poke the printer directly too (takes effect on next login).
sudo usermod -aG lp,dialout "$RUN_USER"

# --- systemd -----------------------------------------------------------------
log "Installing systemd service"
sudo tee /etc/systemd/system/receiptprinter.service >/dev/null <<EOF
[Unit]
Description=Receipt printer service
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$APP_DIR
Environment=NODE_ENV=production
Environment=PORT=$PORT
Environment=PRINTER_DEVICE=$PRINTER_DEVICE
Environment=BOTTOM_PADDING_LINES=4
$EXEC_PRE
ExecStart=$(command -v node) dist/index.js
Restart=on-failure
RestartSec=5
SupplementaryGroups=lp dialout

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable receiptprinter >/dev/null
sudo systemctl restart receiptprinter

# --- Smoke test --------------------------------------------------------------
log "Checking the service"
for _ in $(seq 1 20); do
  curl -fsS "http://localhost:$PORT/healthz" >/dev/null 2>&1 && break
  sleep 1
done
if curl -fsS "http://localhost:$PORT/healthz"; then
  echo
  log "Done! Open http://$(hostname).local:$PORT/ from another machine, or:"
  echo "  curl -X POST http://$(hostname).local:$PORT/print --data 'Hello, receipt!'"
  echo
  echo "Logs:  journalctl -u receiptprinter -f"
else
  warn "Service didn't come up. Recent logs:"
  sudo journalctl -u receiptprinter -n 30 --no-pager
  exit 1
fi
