"""Draws logo.png, the Ministerie van Herverbinding seal. Needs Pillow."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 2400                      # supersampled canvas
C = S / 2
FONT = str(Path(__file__).parent / "controls/fonts/IBMPlexMono-Bold.ttf")
img = Image.new("L", (S, S), 255)
d = ImageDraw.Draw(img)

def ring(r, w):
    d.ellipse([C - r, C - r, C + r, C + r], outline=0, width=w)

# outer seal rings
ring(1150, 44)
ring(1080, 10)
ring(820, 10)

# text on the arc
def arc_text(text, radius, center_deg, size, bottom=False):
    f = ImageFont.truetype(FONT, size)
    widths = [f.getlength(ch) for ch in text]
    spacing = size * 0.12
    total = sum(widths) + spacing * (len(text) - 1)
    span = math.degrees(total / radius)
    a = center_deg - span / 2 if not bottom else center_deg + span / 2
    for ch, w in zip(text, widths):
        step = math.degrees((w + spacing) / radius)
        mid = a + (step / 2 if not bottom else -step / 2) - (math.degrees(spacing / radius) / 2 if not bottom else -math.degrees(spacing / radius) / 2)
        th = math.radians(mid)
        x, y = C + radius * math.cos(th), C + radius * math.sin(th)
        tile = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(tile).text((size, size), ch, font=f, fill=255, anchor="mm")
        rot = -(mid + 90) if not bottom else -(mid - 90)
        tile = tile.rotate(rot, resample=Image.BICUBIC)
        img.paste(0, (int(x - size), int(y - size)), tile)
        a += step if not bottom else -step

arc_text("MINISTERIE VAN HERVERBINDING", 950, -90, 124)
arc_text("OPGERICHT MMXXVI", 950, 90, 110, bottom=True)

# diamonds separating top and bottom text
for ang in (0, 180):
    th = math.radians(ang)
    x, y = C + 950 * math.cos(th), C + 950 * math.sin(th)
    r = 34
    d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=0)

# emblem: growth rings / fingerprint
em = Image.new("L", (S, S), 255)
e = ImageDraw.Draw(em)
def ring_poly(r0, i, grow):
    ox, oy = -i * 5, i * 7          # rings drift off-centre like a real trunk
    pts = []
    for k in range(720):
        th = 2 * math.pi * k / 720
        r = r0 * (1 + 0.025 * math.sin(2 * th + i * 0.6) + 0.012 * math.sin(5 * th + 1.3 + i)) + grow
        pts.append((C + ox + r * math.cos(th), C + oy + r * math.sin(th)))
    return pts

for i in reversed(range(9)):        # outer to inner, each a filled band
    r0 = 78 + i * 70
    e.polygon(ring_poly(r0, i, 14), fill=0)
    e.polygon(ring_poly(r0, i, -14), fill=255)


# the cut: a jagged vertical gap through the rings
gap = []
for k in range(0, 1501, 50):
    y = C - 750 + k
    gap.append((C + (18 if (k // 50) % 2 else -18), y))
left = [(x - 34, y) for x, y in gap]
right = [(x + 34, y) for x, y in reversed(gap)]
e.polygon(left + right, fill=255)

# clip emblem to a circle inside the inner ring
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse([C - 760, C - 760, C + 760, C + 760], fill=255)
img.paste(em, (0, 0), mask)
d.ellipse([C - 30, C - 30, C + 30, C + 30], fill=0)   # the pith, bridging the cut

# stitches across the cut, each with a white halo so it reads over the rings
for dy in (-560, -380, -200, 200, 380, 560):
    y = C + dy
    d.line([(C - 80, y), (C + 80, y)], fill=255, width=64)
    d.line([(C - 70, y), (C + 70, y)], fill=0, width=22)
    for sx in (C - 70, C + 70):
        d.ellipse([sx - 20, y - 20, sx + 20, y + 20], fill=0)

out = img.resize((1200, 1200), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)
out.save(Path(__file__).parent / "logo.png")
