#!/usr/bin/env python3
"""Renders a full receipt as a black-and-white image, 576 dots wide (80mm).

Top: the ministry letterhead with the poem's title as subtitle, then the poem
for the knob values. Below it: the five research departments in random order,
each with its own blank chart to fill in by hand with ink.

Preview without a printer:
  python3 receipt.py 10 10 10 --out preview.png
"""

import math
import random
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

import poems

WIDTH = 576  # printable dots on 80mm paper at 203 dpi
MARGIN = 24
CONTENT = WIDTH - 2 * MARGIN
FONTS = Path(__file__).parent / "fonts"

INK = 0
PAPER = 255


@cache
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"IBMPlex{name}.ttf"), size)


MONO = lambda size: font("Mono-Regular", size)  # noqa: E731
MONO_BOLD = lambda size: font("Mono-Bold", size)  # noqa: E731
SERIF = lambda size: font("Serif-Regular", size)  # noqa: E731
SERIF_ITALIC = lambda size: font("Serif-Italic", size)  # noqa: E731


# --- Drawing helpers --------------------------------------------------------
# Thermal paper has no grey, so the reference's light guides become thin
# dotted lines, and its placeholder shapes become dashed outlines.


def dashed_line(d, x1, y1, x2, y2, dash=4, gap=4, width=1):
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        d.line(
            [(x1 + ux * pos, y1 + uy * pos), (x1 + ux * end, y1 + uy * end)],
            fill=INK,
            width=width,
        )
        pos += dash + gap


def guide_line(d, x1, y1, x2, y2):
    """Light guide: 1-dot dashes with wide gaps."""
    dashed_line(d, x1, y1, x2, y2, dash=2, gap=4, width=1)


def dashed_rect(d, x1, y1, x2, y2):
    for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
        dashed_line(d, *a, *b, dash=4, gap=4, width=2)


def dashed_circle(d, cx, cy, r, segments=None):
    segments = segments or max(8, int(2 * math.pi * r / 8))
    step = 360 / segments
    for i in range(segments):
        start = i * step
        d.arc([cx - r, cy - r, cx + r, cy + r], start, start + step / 2, fill=INK, width=2)


def text_center(d, cx, y, text, f):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=INK)


def wrap(d, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if d.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


# --- Charts -----------------------------------------------------------------
# Each draws into the box (x, y, w, h).

AXIS = 2
LETTERS = "ABCDE"


def bar_chart(d, x, y, w, h):
    left, bottom, top = x + 70, y + h - 30, y + 10
    right = x + w - 70
    for i in range(1, 11):  # squared-paper rows: one per 10%
        gy = bottom - (bottom - top) * i / 10
        guide_line(d, left, gy, right, gy)
    slot = (right - left) / 5
    for i in range(5):
        bx = left + slot * i + slot * 0.25
        dashed_rect(d, bx, top, bx + slot * 0.5, bottom)
        text_center(d, bx + slot * 0.25, bottom + 6, LETTERS[i], MONO(16))
    d.line([(left, top - 6), (left, bottom), (right, bottom)], fill=INK, width=AXIS)


def line_graph(d, x, y, w, h):
    left, bottom, top = x + 70, y + h - 10, y + 10
    right = x + w - 70
    rows, cols = 6, 10
    for i in range(1, rows + 1):
        gy = bottom - (bottom - top) * i / rows
        guide_line(d, left, gy, right, gy)
    for i in range(1, cols + 1):
        gx = left + (right - left) * i / cols
        guide_line(d, gx, top, gx, bottom)
    d.line([(left, top - 6), (left, bottom), (right, bottom)], fill=INK, width=AXIS)


def pictograph(d, x, y, w, h):
    rows, per_row, r, gap = 4, 9, 13, 38
    axis_x = x + 90
    row_h = h / rows
    for row in range(rows):
        cy = y + row_h * row + row_h / 2
        d.text((axis_x - 16, cy), LETTERS[row], font=MONO(16), fill=INK, anchor="rm")
        for i in range(per_row):
            dashed_circle(d, axis_x + 26 + i * gap, cy, r)
    d.line([(axis_x, y), (axis_x, y + h)], fill=INK, width=AXIS)


def pie_chart(d, x, y, w, h):
    r = h / 2 - 8
    cx, cy = x + w / 2, y + h / 2
    for i in range(10):  # ten equal wedges of 10%
        a = math.radians(i * 36 - 90)
        guide_line(d, cx, cy, cx + r * math.cos(a), cy + r * math.sin(a))
    for i in range(20):  # rim ticks every 5%
        a = math.radians(i * 18 - 90)
        inner = r - (10 if i % 2 == 0 else 5)
        d.line(
            [(cx + inner * math.cos(a), cy + inner * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a))],
            fill=INK,
            width=2,
        )
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=AXIS)


def dot_plot(d, x, y, w, h):
    left, right = x + 60, x + w - 60
    base = y + h - 30
    ticks = 11
    for i in range(ticks):
        tx = left + (right - left) * i / (ticks - 1)
        d.line([(tx, base), (tx, base + 8)], fill=INK, width=AXIS)
        text_center(d, tx, base + 10, str(i), MONO(14))
        guide_line(d, tx, y + 10, tx, base - 4)  # stacking column
    d.line([(left - 12, base), (right + 12, base)], fill=INK, width=AXIS)


# --- Departments ------------------------------------------------------------


@dataclass
class Department:
    number: int
    name: str
    description: str
    chart: Callable
    chart_name: str
    instruction: str
    chart_height: int = 230


DEPARTMENTS = [
    Department(
        1,
        "UITGESTORVEN GEWOONTES",
        "De afdeling onderzoekt welke menselijke vermogens en gewoontes langzaam lijken te verdwijnen.",
        bar_chart,
        "Staafdiagram",
        "Kleur elke staaf in. Eén hokje = 10%.",
    ),
    Department(
        2,
        "ECOSYSTEEMINTEGRATIE",
        "Deze afdeling doet onderzoek naar de mens als onderdeel van het ecosysteem.",
        pie_chart,
        "Cirkeldiagram",
        "Arceer de delen naar aandeel. Eén vak = 10%.",
    ),
    Department(
        3,
        "NERVOSITEITSREDUCTIE",
        "Deze afdeling onderzoekt of het menselijke zenuwstelsel nog zelfstandig kan terugkeren"
        " naar een toestand van rust.",
        line_graph,
        "Lijngrafiek",
        "Zet de punten, verbind ze daarna met een liniaal.",
    ),
    Department(
        4,
        "SYMBIOSE & WEDERKERIGHEID",
        "Deze afdeling onderzoekt in hoeverre menselijke individuen nog in staat zijn tot"
        " wederzijdse afhankelijkheid.",
        pictograph,
        "Pictogram",
        "Eén symbool = ____ . Teken halve symbolen voor de rest.",
    ),
    Department(
        5,
        "VERWONDERINGSONDERZOEK",
        "Deze afdeling onderzoekt meetbare menselijke respons op verschijnselen zonder directe"
        " functionele waarde.",
        dot_plot,
        "Stippendiagram",
        "Eén stip per telling, gestapeld boven het getal.",
    ),
]


# --- Layout -----------------------------------------------------------------


class Canvas:
    """A tall page we draw down, cropped to the used height at the end."""

    def __init__(self, max_height=6000):
        self.img = Image.new("L", (WIDTH, max_height), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.y = MARGIN

    def space(self, h):
        self.y += h

    def text(self, text, f, line_height, center=False):
        for line in wrap(self.d, text, f, CONTENT):
            if center:
                text_center(self.d, WIDTH / 2, self.y, line, f)
            else:
                self.d.text((MARGIN, self.y), line, font=f, fill=INK)
            self.y += line_height

    def rule(self, width=2, dashed=False):
        if dashed:
            dashed_line(self.d, MARGIN, self.y, WIDTH - MARGIN, self.y, dash=6, gap=6, width=width)
        else:
            self.d.line([(MARGIN, self.y), (WIDTH - MARGIN, self.y)], fill=INK, width=width)

    def finish(self) -> Image.Image:
        img = self.img.crop((0, 0, WIDTH, self.y + MARGIN))
        # Hard threshold: the printer has only black and white.
        return img.point(lambda v: PAPER if v > 140 else INK).convert("1")


def draw_header(c: Canvas, subtitle: str):
    c.rule(width=4)
    c.space(16)
    c.text("MINISTERIE VAN", MONO_BOLD(40), 48, center=True)
    c.text("HERVERBINDING", MONO_BOLD(40), 48, center=True)
    c.space(10)
    c.rule(width=1)
    c.space(16)
    c.text(subtitle, MONO_BOLD(28), 38, center=True)


def draw_poem(c: Canvas, values, rng):
    title, stanzas = poems.poem(values, rng)
    draw_header(c, title)
    c.space(18)
    for i, stanza in enumerate(stanzas):
        if i:
            c.space(20)
        for line in stanza:
            c.text(line, SERIF(23), 31)


def draw_department(c: Canvas, dep: Department):
    c.rule(width=3)
    c.space(14)
    c.text(f"AFDELING {dep.number}", MONO(18), 26)
    c.text(dep.name, MONO_BOLD(26), 34)
    c.space(4)
    c.text(dep.description, SERIF_ITALIC(20), 27)
    c.space(18)
    dep.chart(c.d, MARGIN, c.y, CONTENT, dep.chart_height)
    c.space(dep.chart_height + 18)
    c.text(dep.chart_name, MONO_BOLD(19), 26, center=True)
    c.text(dep.instruction, SERIF(18), 24, center=True)
    c.space(30)


def render(values: list[int], rng: random.Random | None = None) -> Image.Image:
    rng = rng or random.Random()
    c = Canvas()
    draw_poem(c, values, rng)
    c.space(40)
    for dep in rng.sample(DEPARTMENTS, len(DEPARTMENTS)):
        draw_department(c, dep)
    c.rule(width=3)
    return c.finish()


if __name__ == "__main__":
    args = sys.argv[1:]
    out = "preview.png"
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        del args[i : i + 2]
    knobs = [int(v) for v in args[:3]] or [10, 10, 10]
    img = render(knobs)
    img.save(out)
    print(f"{out}: {img.width}x{img.height} dots, {img.height / 8:.0f} mm long")
