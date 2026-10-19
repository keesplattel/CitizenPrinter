"""Draws the Ministerie van Herverbinding seal as logo.png and logo.svg.

Needs Pillow and fontTools (pip install pillow fonttools). The SVG has its
lettering converted to outlines, so it looks the same without the font.
"""
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
S = 2400                      # supersampled canvas
C = S / 2
FONT = str(HERE / "controls/fonts/IBMPlexMono-Bold.ttf")

# --- Shared geometry ------------------------------------------------------

SEAL_RINGS = [(1150, 44), (1080, 10), (820, 10)]   # (radius, stroke width)
TEXT_RADIUS = 950
TEXTS = [  # text, centre angle, size, along the bottom
    ("MINISTERIE VAN HERVERBINDING", -90, 124, False),
    ("OPGERICHT MMXXVI", 90, 110, True),
]
EMBLEM_RADIUS = 760
PITH = 30
STITCHES = (-560, -380, -200, 200, 380, 560)


def arc_layout(text, radius, center_deg, size, bottom=False):
    """Yield (char, x, y, rotation in degrees clockwise) for text on a circle."""
    f = ImageFont.truetype(FONT, size)
    widths = [f.getlength(ch) for ch in text]
    spacing = size * 0.12
    total = sum(widths) + spacing * (len(text) - 1)
    span = math.degrees(total / radius)
    a = center_deg - span / 2 if not bottom else center_deg + span / 2
    for ch, w in zip(text, widths):
        step = math.degrees((w + spacing) / radius)
        half_gap = math.degrees(spacing / radius) / 2
        mid = a + step / 2 - half_gap if not bottom else a - step / 2 + half_gap
        th = math.radians(mid)
        yield ch, C + radius * math.cos(th), C + radius * math.sin(th), (mid + 90 if not bottom else mid - 90)
        a += step if not bottom else -step


def diamonds():
    for ang in (0, 180):
        th = math.radians(ang)
        x, y = C + TEXT_RADIUS * math.cos(th), C + TEXT_RADIUS * math.sin(th)
        r = 34
        yield [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]


def ring_poly(r0, i, grow):
    ox, oy = -i * 5, i * 7          # rings drift off-centre like a real trunk
    pts = []
    for k in range(720):
        th = 2 * math.pi * k / 720
        r = r0 * (1 + 0.025 * math.sin(2 * th + i * 0.6) + 0.012 * math.sin(5 * th + 1.3 + i)) + grow
        pts.append((C + ox + r * math.cos(th), C + oy + r * math.sin(th)))
    return pts


def growth_rings():
    """Outer to inner: (outer edge, inner edge) of each filled band."""
    for i in reversed(range(9)):
        r0 = 78 + i * 70
        yield ring_poly(r0, i, 14), ring_poly(r0, i, -14)


def cut_poly():
    """The cut: a jagged vertical gap through the rings."""
    gap = []
    for k in range(0, 1501, 50):
        y = C - 750 + k
        gap.append((C + (18 if (k // 50) % 2 else -18), y))
    return [(x - 34, y) for x, y in gap] + [(x + 34, y) for x, y in reversed(gap)]


# --- PNG ------------------------------------------------------------------


def draw_png():
    img = Image.new("L", (S, S), 255)
    d = ImageDraw.Draw(img)
    for r, w in SEAL_RINGS:
        d.ellipse([C - r, C - r, C + r, C + r], outline=0, width=w)

    for text, deg, size, bottom in TEXTS:
        f = ImageFont.truetype(FONT, size)
        for ch, x, y, rot in arc_layout(text, TEXT_RADIUS, deg, size, bottom):
            tile = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(tile).text((size, size), ch, font=f, fill=255, anchor="mm")
            tile = tile.rotate(-rot, resample=Image.BICUBIC)
            img.paste(0, (int(x - size), int(y - size)), tile)
    for poly in diamonds():
        d.polygon(poly, fill=0)

    em = Image.new("L", (S, S), 255)
    e = ImageDraw.Draw(em)
    for outer, inner in growth_rings():
        e.polygon(outer, fill=0)
        e.polygon(inner, fill=255)
    e.polygon(cut_poly(), fill=255)
    mask = Image.new("L", (S, S), 0)
    r = EMBLEM_RADIUS
    ImageDraw.Draw(mask).ellipse([C - r, C - r, C + r, C + r], fill=255)
    img.paste(em, (0, 0), mask)
    d.ellipse([C - PITH, C - PITH, C + PITH, C + PITH], fill=0)   # the pith, bridging the cut

    # stitches across the cut, each with a white halo so it reads over the rings
    for dy in STITCHES:
        y = C + dy
        d.line([(C - 80, y), (C + 80, y)], fill=255, width=64)
        d.line([(C - 70, y), (C + 70, y)], fill=0, width=22)
        for sx in (C - 70, C + 70):
            d.ellipse([sx - 20, y - 20, sx + 20, y + 20], fill=0)

    out = img.resize((1200, 1200), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)
    out.save(HERE / "logo.png")


# --- SVG ------------------------------------------------------------------


def path(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


def draw_svg():
    font = TTFont(FONT)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    # Pillow's "mm" anchor: halfway between ascender and descender.
    v_mid = (font["hhea"].ascent + font["hhea"].descent) / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="1200" height="1200">',
        "<title>Ministerie van Herverbinding</title>",
        f'<rect width="{S}" height="{S}" fill="#fff"/>',
    ]
    for r, w in SEAL_RINGS:
        out.append(f'<circle cx="{C}" cy="{C}" r="{r - w / 2}" fill="none" stroke="#000" stroke-width="{w}"/>')

    for text, deg, size, bottom in TEXTS:
        s = size / upm
        for ch, x, y, rot in arc_layout(text, TEXT_RADIUS, deg, size, bottom):
            name = cmap[ord(ch)]
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(pen)
            if not pen.getCommands():
                continue  # space
            adv = glyphs[name].width
            out.append(
                f'<path transform="translate({x:.2f},{y:.2f}) rotate({rot:.3f}) '
                f'translate({-adv * s / 2:.2f},{v_mid * s:.2f}) scale({s:.5f},{-s:.5f})" '
                f'd="{pen.getCommands()}"/>'
            )
    for poly in diamonds():
        out.append(f'<path d="{path(poly)}"/>')

    out.append(f'<clipPath id="emblem"><circle cx="{C}" cy="{C}" r="{EMBLEM_RADIUS}"/></clipPath>')
    out.append('<g clip-path="url(#emblem)">')
    for outer, inner in growth_rings():
        out.append(f'<path fill-rule="evenodd" d="{path(outer)} {path(inner)}"/>')
    out.append(f'<path fill="#fff" d="{path(cut_poly())}"/>')
    out.append("</g>")
    out.append(f'<circle cx="{C}" cy="{C}" r="{PITH}"/>')

    for dy in STITCHES:
        y = C + dy
        out.append(f'<line x1="{C - 80}" y1="{y}" x2="{C + 80}" y2="{y}" stroke="#fff" stroke-width="64"/>')
        out.append(f'<line x1="{C - 70}" y1="{y}" x2="{C + 70}" y2="{y}" stroke="#000" stroke-width="22"/>')
        for sx in (C - 70, C + 70):
            out.append(f'<circle cx="{sx}" cy="{y}" r="20"/>')

    out.append("</svg>")
    (HERE / "logo.svg").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    draw_png()
    draw_svg()
