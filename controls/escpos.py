"""Turns a black-and-white image into ESC/POS bytes for a thermal printer."""

from PIL import Image, ImageOps

ESC, GS = b"\x1b", b"\x1d"
INIT = ESC + b"@"
CUT = GS + b"VA\x00"  # feed to the cutter, then partial cut
BAND = 128  # rows per raster command; keeps each chunk small for the printer


def raster(img: Image.Image) -> bytes:
    """Encode an image as `GS v 0` raster bands (1 bit = 1 black dot)."""
    if img.width % 8:
        raise ValueError("image width must be a multiple of 8")
    # Pillow's 1-bit packing uses 1 for white; ESC/POS uses 1 for black.
    bits = ImageOps.invert(img.convert("L")).convert("1")
    width_bytes = img.width // 8
    out = bytearray()
    for top in range(0, img.height, BAND):
        band = bits.crop((0, top, img.width, min(top + BAND, img.height)))
        out += GS + b"v0\x00"
        out += bytes([width_bytes & 0xFF, width_bytes >> 8, band.height & 0xFF, band.height >> 8])
        out += band.tobytes()
    return bytes(out)


def receipt(img: Image.Image, feed_lines: int = 4) -> bytes:
    return INIT + raster(img) + ESC + b"d" + bytes([feed_lines]) + CUT
