"""Пиксельный фреймбуфер: всё приложение рисуется по пикселям.

Буфер - плоский список 24-битных цветов. Наружу отдаётся либо строка
для tkinter.PhotoImage.put(), либо PNG (только stdlib, без Pillow).
"""
from __future__ import annotations

import struct
import zlib

from .pixelfont import BIG_DIGITS, FONT3x5, FONT5x7, text_width

TRANSPARENT = -1


def rgb(color) -> int:
    """'#rrggbb' | '#rgb' | int -> int."""
    if isinstance(color, int):
        return color
    s = color.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return int(s, 16)


def hexstr(c: int) -> str:
    return "#%06x" % c


def mix(a, b, t: float) -> int:
    """Линейная интерполяция двух цветов, t=0 -> a, t=1 -> b."""
    a, b = rgb(a), rgb(b)
    out = 0
    for shift in (16, 8, 0):
        ca = (a >> shift) & 0xFF
        cb = (b >> shift) & 0xFF
        out |= int(ca + (cb - ca) * t) << shift
    return out


def shade(color, amount: float) -> int:
    """amount < 0 - темнее, > 0 - светлее."""
    return mix(color, 0x000000 if amount < 0 else 0xFFFFFF, abs(amount))


class Framebuffer:
    def __init__(self, width: int, height: int, bg=0x000000):
        self.w = width
        self.h = height
        self.buf = [rgb(bg)] * (width * height)

    # --- базовые операции -------------------------------------------------
    def fill(self, color):
        c = rgb(color)
        self.buf = [c] * (self.w * self.h)

    def px(self, x: int, y: int, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.buf[y * self.w + x] = rgb(color)

    def get(self, x: int, y: int) -> int:
        return self.buf[y * self.w + x]

    def hline(self, x, y, length, color):
        if not (0 <= y < self.h):
            return
        x0 = max(0, x)
        x1 = min(self.w, x + length)
        if x1 <= x0:
            return
        c = rgb(color)
        base = y * self.w
        self.buf[base + x0:base + x1] = [c] * (x1 - x0)

    def vline(self, x, y, length, color):
        c = rgb(color)
        for yy in range(max(0, y), min(self.h, y + length)):
            self.buf[yy * self.w + x] = c if 0 <= x < self.w else self.buf[yy * self.w + x]

    def rect(self, x, y, w, h, color):
        for yy in range(h):
            self.hline(x, y + yy, w, color)

    def frame(self, x, y, w, h, color):
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def checker(self, x, y, w, h, c1, c2, size=2):
        for yy in range(h):
            for xx in range(w):
                c = c1 if ((xx // size + yy // size) % 2 == 0) else c2
                self.px(x + xx, y + yy, c)

    def scanlines(self, x, y, w, h, color, step=3):
        for yy in range(0, h, step):
            self.hline(x, y + yy, w, color)

    def dots(self, x, y, w, h, color, step=4):
        for yy in range(0, h, step):
            for xx in range(0, w, step):
                self.px(x + xx, y + yy, color)

    def gradient_v(self, x, y, w, h, top, bottom):
        for yy in range(h):
            t = yy / max(1, h - 1)
            self.hline(x, y + yy, w, mix(top, bottom, t))

    # --- скруглённая панель с «пиксельной» тенью --------------------------
    def panel(self, x, y, w, h, fill, border=None, shadow=None, radius=2, inner_top=None):
        if shadow is not None:
            self._round_rect(x + 2, y + 2, w, h, shadow, radius)
        self._round_rect(x, y, w, h, fill, radius)
        if inner_top is not None:
            self.hline(x + radius, y + 1, w - radius * 2, inner_top)
        if border is not None:
            self._round_outline(x, y, w, h, border, radius)

    def _round_rect(self, x, y, w, h, color, r):
        for yy in range(h):
            inset = self._inset(yy, h, r)
            self.hline(x + inset, y + yy, w - inset * 2, color)

    @staticmethod
    def _inset(yy, h, r):
        if yy < r:
            return max(0, min(r - yy - (1 if r > 1 else 0), r))
        if yy >= h - r:
            return max(0, min(yy - (h - r) + (1 if r > 1 else 0), r))
        return 0

    def _round_outline(self, x, y, w, h, color, r):
        for yy in range(h):
            ins = self._inset(yy, h, r)
            if yy == 0 or yy == h - 1:
                self.hline(x + ins, y + yy, w - ins * 2, color)
                continue
            prev_ins = self._inset(yy - 1, h, r)
            next_ins = self._inset(yy + 1, h, r)
            if ins < prev_ins:  # верхний скос
                self.hline(x + ins, y + yy, prev_ins - ins + 1, color)
                self.hline(x + w - 1 - prev_ins, y + yy, prev_ins - ins + 1, color)
            if ins < next_ins:  # нижний скос
                self.hline(x + ins, y + yy, next_ins - ins + 1, color)
                self.hline(x + w - 1 - next_ins, y + yy, next_ins - ins + 1, color)
            self.px(x + ins, y + yy, color)
            self.px(x + w - 1 - ins, y + yy, color)

    # --- текст ------------------------------------------------------------
    def text(self, x, y, s, color, font=FONT5x7, spacing=1, shadow=None, scale=1):
        cx = x
        for ch in str(s):
            g = font.get(ch) or font.get(ch.upper()) or font.get("?")
            gw = len(g[0])
            for row, bits in enumerate(g):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        px0 = cx + col * scale
                        py0 = y + row * scale
                        if shadow is not None:
                            self.rect(px0 + scale, py0 + scale, scale, scale, shadow)
                        self.rect(px0, py0, scale, scale, color)
            cx += (gw + spacing) * scale
        return cx - x - spacing * scale

    def text_center(self, cx, y, s, color, font=FONT5x7, spacing=1, shadow=None, scale=1):
        w = text_width(s, font, spacing) * scale
        return self.text(cx - w // 2, y, s, color, font, spacing, shadow, scale)

    def text_right(self, x_right, y, s, color, font=FONT5x7, spacing=1, shadow=None, scale=1):
        w = text_width(s, font, spacing) * scale
        return self.text(x_right - w, y, s, color, font, spacing, shadow, scale)

    def big_text(self, x, y, s, color, spacing=1, shadow=None):
        return self.text(x, y, s, color, font=BIG_DIGITS, spacing=spacing, shadow=shadow)

    def tiny(self, x, y, s, color, spacing=1, shadow=None):
        return self.text(x, y, s, color, font=FONT3x5, spacing=spacing, shadow=shadow)

    # --- спрайты ----------------------------------------------------------
    def sprite(self, x, y, rows, palette, scale=1, flip=False):
        for ry, row in enumerate(rows):
            if flip:
                row = row[::-1]
            for rx, ch in enumerate(row):
                if ch == "." or ch == " ":
                    continue
                color = palette.get(ch)
                if color is None:
                    continue
                if scale == 1:
                    self.px(x + rx, y + ry, color)
                else:
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, color)

    # --- вывод ------------------------------------------------------------
    def to_tk_data(self, cache=None):
        cache = cache if cache is not None else {}
        buf = self.buf
        w = self.w
        rows = []
        for y in range(self.h):
            row = buf[y * w:(y + 1) * w]
            out = []
            for c in row:
                s = cache.get(c)
                if s is None:
                    s = cache[c] = "#%06x" % c
                out.append(s)
            rows.append("{" + " ".join(out) + "}")
        return " ".join(rows)

    def to_png(self, path, scale=1):
        raw = bytearray()
        for y in range(self.h):
            line = bytearray()
            for x in range(self.w):
                c = self.buf[y * self.w + x]
                px = bytes(((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)) * scale
                line += px
            for _ in range(scale):
                raw += b"\x00" + line

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w * scale, self.h * scale, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as fh:
            fh.write(png)
        return path
