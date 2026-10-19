# CitizenPrinter

A Raspberry Pi with three knobs and a button that prints receipts on a Citizen
80mm thermal printer. Each receipt starts with a short poem about losing touch
with nature and trying to find the way back (the knobs steer it), followed by
five research departments in random order, each with a blank chart to fill in
by hand with ink.

| Department | Chart |
|---|---|
| 1 Uitgestorven gewoontes | bar chart |
| 2 Ecosysteemintegratie | pie chart |
| 3 Nervositeitsreductie | line graph |
| 4 Symbiose & wederkerigheid | pictograph |
| 5 Verwonderingsonderzoek | dot plot |

| Knob | Controls | Low → high |
|---|---|---|
| 1 | Wildness (where the poem is set) | city → suburb → edge of town → wild |
| 2 | Season | winter → spring → summer → autumn |
| 3 | Hope (how it ends) | lost → unsure → hopeful → found |

Each knob runs 0–20 and starts at 10; pushing a knob resets it to 10. The
button LED is on when ready, blinks while printing, and flashes fast on an
error.

## How it fits together

- **Controls**: `controls/controller.py` reads the knobs and button (gpiozero),
  renders the receipt as an image (`receipt.py`: poem from `poems.py` plus the
  department charts) and writes it to the printer as ESC/POS raster data
  (`escpos.py`).
- **Print service** (optional): [dandriscoll/receiptprinter](https://github.com/dandriscoll/receiptprinter),
  installed by `install.sh`, gives a web form and `POST :4180/print` for
  plain-text printing. The button doesn't use it.

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

Preview a whole receipt as an image (needs Pillow: `pip install pillow`):

```bash
python3 controls/receipt.py 10 10 10 --out preview.png
```

The departments and their charts are in the `DEPARTMENTS` list in
`controls/receipt.py`.

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

Set `DRY_RUN=1` in `/etc/systemd/system/receiptcontrols.service`, then
`sudo systemctl daemon-reload && sudo systemctl restart receiptcontrols`. Each
press then saves the receipt as `~/CitizenPrinter/last-print.png` instead of
printing.
