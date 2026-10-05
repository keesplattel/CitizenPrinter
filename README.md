# CitizenPrinter

A Raspberry Pi with three knobs and a button that prints poems on a Citizen
80mm thermal receipt printer. The poems are about losing touch with nature and
trying to find the way back; the knobs steer them, and every press prints a
new one.

| Knob | Controls | Low → high |
|---|---|---|
| 1 | Wildness (where the poem is set) | city → suburb → edge of town → wild |
| 2 | Season | winter → spring → summer → autumn |
| 3 | Hope (how it ends) | lost → unsure → hopeful → found |

Each knob runs 0–20 and starts at 10; pushing a knob resets it to 10. The
button LED is on when ready, blinks while printing, and flashes fast on an
error.

## How it fits together

- **Print service**: [dandriscoll/receiptprinter](https://github.com/dandriscoll/receiptprinter),
  installed by `install.sh`. It takes text on `POST :4180/print` and sends it
  to the printer.
- **Controls**: `controls/controller.py` reads the knobs and button (gpiozero)
  and posts a poem from `controls/poems.py` to the print service.

## Install on the Pi

```bash
git clone https://github.com/keesplattel/CitizenPrinter ~/CitizenPrinter
bash ~/CitizenPrinter/install.sh            # print service
bash ~/CitizenPrinter/install-controls.sh   # knobs + button
```

## Update

```bash
bash ~/CitizenPrinter/update.sh
```

## Writing poems

The line banks live in `controls/poems.py`. Every entry is a two-line couplet
that forms a complete sentence, so any combination reads correctly. Keep lines
under ~42 characters and use plain ASCII (no curly quotes or long dashes, as the
printer can't print them).

Try poems without the hardware:

```bash
python3 controls/poems.py 10 10 10   # knob values
python3 controls/poems.py --samples  # a spread from low to high
```

## Wiring (BCM GPIO / physical pin)

| Part | S1 (CLK) | S2 (DT) | SW | + | GND |
|---|---|---|---|---|---|
| Encoder 1 | 17 / 11 | 27 / 13 | 22 / 15 | 3.3V / 1 | 9 |
| Encoder 2 | 5 / 29 | 6 / 31 | 13 / 33 | 3.3V / 17 | 25 |
| Encoder 3 | 19 / 35 | 26 / 37 | 21 / 40 | 3.3V / 17 | 39 |

- Button switch: GPIO 23 (pin 16) and GND (pin 14)
- Button LED: GPIO 24 (pin 18) → 330Ω → LED+, LED− → GND (pin 20)

Power the encoders from 3.3V, never 5V.

## Testing without a printer

```bash
sudo mkdir -p /etc/systemd/system/receiptprinter.service.d
printf "[Service]\nEnvironment=DRY_RUN=1\n" | sudo tee /etc/systemd/system/receiptprinter.service.d/dry-run.conf
sudo systemctl daemon-reload && sudo systemctl restart receiptprinter
journalctl -a -u receiptprinter -f
```

Delete `dry-run.conf` and restart to print on paper again.
