#!/usr/bin/env bash
# Installs the encoder/button controller (controls/controller.py) as a systemd
# service that runs straight from this git checkout, so `update.sh` (git pull +
# restart) is all an update needs. Run on the Pi as your normal user, after
# install.sh.
set -euo pipefail

RUN_USER="$(id -un)"
CONTROLS_DIR="$(cd "$(dirname "$0")" && pwd)/controls"

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as your normal user, not root (it calls sudo itself)." >&2
  exit 1
fi

log "Installing gpiozero and Pillow"
sudo apt-get update -qq
sudo apt-get install -y -qq python3-gpiozero python3-pil
# lgpio is the preferred GPIO backend on current Raspberry Pi OS; older
# releases fall back to RPi.GPIO.
sudo apt-get install -y -qq python3-lgpio 2>/dev/null || sudo apt-get install -y -qq python3-rpi.gpio

sudo usermod -aG gpio,lp,dialout "$RUN_USER"

# Citizen printers show up as a USB printer (/dev/usb/lp0) or, in their
# "virtual COM" mode, as a serial device (/dev/ttyACM0).
PRINTER_DEVICE=/dev/usb/lp0
for dev in /dev/usb/lp0 /dev/usb/lp1 /dev/ttyACM0 /dev/ttyUSB0; do
  if [ -e "$dev" ]; then PRINTER_DEVICE="$dev"; break; fi
done
log "Printing to $PRINTER_DEVICE"

log "Installing systemd service"
sudo tee /etc/systemd/system/receiptcontrols.service >/dev/null <<EOF
[Unit]
Description=Receipt printer encoders and button

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$CONTROLS_DIR
Environment=PYTHONUNBUFFERED=1
Environment=PRINTER_DEVICE=$PRINTER_DEVICE
# Set to 1 to save each receipt as last-print.png instead of printing.
Environment=DRY_RUN=0
# Override pins here if needed (BCM numbers, S1,S2,SW):
# Environment=ENC1_PINS=17,27,22
# Environment=BUTTON_PIN=23
# Environment=LED_PIN=24
ExecStart=/usr/bin/python3 $CONTROLS_DIR/controller.py
Restart=on-failure
RestartSec=3
SupplementaryGroups=gpio lp dialout

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable receiptcontrols >/dev/null
sudo systemctl restart receiptcontrols
sleep 3
sudo systemctl --no-pager status receiptcontrols | head -15

log "Done. Turn the knobs and watch: journalctl -u receiptcontrols -f"
