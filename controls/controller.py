#!/usr/bin/env python3
"""Physical controls for the receipt printer.

Three rotary encoders set values 0..KNOB_MAX (wildness, season, hope); the
button prints a receipt for them: a poem (poems.py) and the five department
charts (receipt.py), rendered as an image and written straight to the printer
device. Pushing an encoder resets it to the middle. The button LED is on when
ready, blinks while printing, and flashes fast after an error.

Pins are BCM numbers and can be overridden with environment variables. Set
DRY_RUN=1 to save each receipt as a PNG (PREVIEW_PATH) instead of printing.
"""

import logging
import os
import signal
import threading
import tty
from pathlib import Path

from gpiozero import LED, Button, RotaryEncoder

import escpos
import poems
import receipt

PRINTER_DEVICE = os.environ.get("PRINTER_DEVICE", "/dev/usb/lp0")
DRY_RUN = os.environ.get("DRY_RUN", "0") in ("1", "true")
PREVIEW_PATH = Path(os.environ.get("PREVIEW_PATH", Path(__file__).parent.parent / "last-print.png"))

# (S1/CLK, S2/DT, SW) per encoder
ENCODER_PINS = [
    tuple(int(p) for p in os.environ.get(f"ENC{i}_PINS", default).split(","))
    for i, default in enumerate(["17,27,22", "5,6,13", "19,26,21"], start=1)
]
BUTTON_PIN = int(os.environ.get("BUTTON_PIN", "23"))
LED_PIN = int(os.environ.get("LED_PIN", "24"))
KNOB_START = poems.KNOB_MAX // 2

log = logging.getLogger("controls")


def print_receipt(values: list[int]) -> None:
    img = receipt.render(values)
    if DRY_RUN:
        img.save(PREVIEW_PATH)
        log.info("dry run: saved %s (%dx%d)", PREVIEW_PATH, img.width, img.height)
        return
    data = escpos.receipt(img)
    with open(PRINTER_DEVICE, "wb") as dev:
        if dev.isatty():
            # Serial-mode printers (/dev/ttyACM0): pass bytes through untouched.
            tty.setraw(dev.fileno())
        dev.write(data)
    log.info("printed %d bytes to %s", len(data), PRINTER_DEVICE)


class Controls:
    def __init__(self) -> None:
        # max_steps=0: unbounded, read the raw .steps count.
        self.encoders = [RotaryEncoder(a, b, max_steps=0) for a, b, _ in ENCODER_PINS]
        for enc in self.encoders:
            enc.steps = KNOB_START
        self.encoder_buttons = [Button(sw, bounce_time=0.05) for _, _, sw in ENCODER_PINS]
        self.button = Button(BUTTON_PIN, bounce_time=0.05)
        self.led = LED(LED_PIN)
        self.printing = threading.Lock()

        for i, (enc, sw) in enumerate(zip(self.encoders, self.encoder_buttons), start=1):
            enc.when_rotated = lambda enc=enc, i=i: self.rotated(enc, i)
            sw.when_pressed = lambda enc=enc, i=i: self.reset(enc, i)
        self.button.when_pressed = self.print_values
        self.led.on()

    @property
    def values(self) -> list[int]:
        return [enc.steps for enc in self.encoders]

    def rotated(self, enc: RotaryEncoder, i: int) -> None:
        # Stop at the ends, so turning back responds immediately.
        enc.steps = max(0, min(poems.KNOB_MAX, enc.steps))
        log.info("encoder %d -> %d", i, enc.steps)

    def reset(self, enc: RotaryEncoder, i: int) -> None:
        enc.steps = KNOB_START
        log.info("encoder %d reset to %d", i, KNOB_START)

    def print_values(self) -> None:
        if not self.printing.acquire(blocking=False):
            return  # already printing; ignore extra presses
        try:
            self.led.blink(on_time=0.15, off_time=0.15)
            log.info("printing %s", self.values)
            print_receipt(self.values)
            self.led.on()
        except Exception:
            log.exception("print failed")
            self.led.blink(on_time=0.05, off_time=0.05, n=30, background=False)
            self.led.on()
        finally:
            self.printing.release()


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    controls = Controls()
    log.info("ready: encoders %s, button %d, led %d", ENCODER_PINS, BUTTON_PIN, LED_PIN)

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()
    controls.led.off()


if __name__ == "__main__":
    main()
