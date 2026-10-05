#!/usr/bin/env bash
# Pulls the latest poems/controller from GitHub and restarts the controls.
# Run on the Pi: bash ~/CitizenPrinter/update.sh
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
sudo systemctl restart receiptcontrols
sleep 2
systemctl --no-pager status receiptcontrols | head -5
