"""Пиксельные виджеты: тайлы метрик, графики, бейджи, кнопки, идентиконы."""
from __future__ import annotations

import hashlib

from .fb import mix, rgb, shade
from .ghclient import human
from .pixelfont import FONT3x5, FONT5x7, text_width
from .sprites import SPRITES, resolve_palette

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Rust": "#dea584", "Go": "#00ADD8", "C": "#555555", "C++": "#f34b7d",
    "Java": "#b07219", "Shell": "#89e051", "HTML": "#e34c26", "CSS": "#563d7c",
    "Ruby": "#701516", "Zig": "#ec915c", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Dockerfile": "#384d54", "Makefile": "#427819", "Make": "#427819",
    "C#": "#178600", "PHP": "#4F5D95", "Lua": "#000080", "Vim script": "#199f4b",
    "Nix": "#7e7eff", "Elixir": "#6e4a7e", "Haskell": "#5e5086", "Scala": "#c22d40",
    "Perl": "#0298c3", "Dart": "#00B4AB", "Julia": "#a270ba", "R": "#198CE7",
    "Assembly": "#6E4C13", "Objective-C": "#438eff", "TeX": "#3D6117",
    "Jupyter Notebook": "#DA5B0B", "Markdown": "#083fa1", "CMake": "#DA3434",
    "PowerShell": "#012456", "Vue": "#41b883", "Svelte": "#ff3e00",
    "HCL": "#844FBA", "SCSS": "#c6538c", "Sass": "#a53b70", "Nim": "#ffc200",
    "Erlang": "#B83998", "Clojure": "#db5855", "OCaml": "#3be133",
    "Solidity": "#AA6746", "Batchfile": "#C1F12E", "Groovy": "#4298b8",
}


def lang_color(name, theme):
    return LANG_COLORS.get(name, theme["accent2"])


def pal(theme, extra=None):
    return resolve_palette(theme, extra)


def icon(fb, x, y, name, theme, scale=1, extra=None):
    if name not in SPRITES:
        return
    fb.sprite(x, y, SPRITES[name], pal(theme, extra), scale=scale)


# ------------------------------------------------------------------ базовое
def badge(fb, x, y, text, theme, bg=None, fg=None, tiny=True):
    font = FONT3x5 if tiny else FONT5x7
    tw = text_width(text, font)
    h = (len(next(iter(font.values()))) + 4)
    w = tw + 6
    fb.panel(x, y, w, h, bg or theme["panel2"], radius=1)
    fb.text(x + 3, y + 2, text, fg or theme["fg"], font=font)
    return w


def button(fb, x, y, w, h, key, label, theme, active=False, hot=False):
    face = theme["accent"] if active else theme["panel2"]
    txt = theme["bg"] if active else theme["fg"]
    fb.panel(x, y, w, h, face, border=theme["border"], shadow=theme["shadow"], radius=1)
    fb.text(x + 4, y + (h - 5) // 2, "[%s]" % key, theme["bg"] if active else theme["accent"], font=FONT3x5)
    fb.text(x + 4 + text_width("[%s]" % key, FONT3x5) + 3, y + (h - 5) // 2, label, txt, font=FONT3x5)
    if hot:
        fb.px(x + w - 3, y + 2, theme["star"])
    return w


def progress(fb, x, y, w, h, ratio, theme, color=None, track=None):
    ratio = max(0.0, min(1.0, ratio))
    fb.rect(x, y, w, h, track or theme["grid"])
    filled = int(round(w * ratio))
    if filled:
        fb.rect(x, y, filled, h, color or theme["accent"])
        fb.hline(x, y, filled, shade(color or theme["accent"], 0.25))
    fb.frame(x - 1, y - 1, w + 2, h + 2, theme["border"])


def identicon(fb, x, y, seed, theme, scale=2, size=5):
    """Симметричный пиксельный аватар из хэша имени."""
    h = hashlib.sha1(seed.encode()).digest()
    base = rgb("#%02x%02x%02x" % (0x50 + h[0] % 0xB0, 0x50 + h[1] % 0xB0, 0x50 + h[2] % 0xB0))
    alt = mix(base, theme["fg"], 0.4)
    fb.rect(x, y, size * scale, size * scale, theme["panel2"])
    half = size // 2 + 1
    for cx in range(half):
        for cy in range(size):
            byte = h[(cx * size + cy) % len(h)]
            if byte % 5 < 3:
                c = base if byte % 2 else alt
                fb.rect(x + cx * scale, y + cy * scale, scale, scale, c)
                fb.rect(x + (size - 1 - cx) * scale, y + cy * scale, scale, scale, c)
    fb.frame(x - 1, y - 1, size * scale + 2, size * scale + 2, theme["border"])


# ------------------------------------------------------------------ тайлы
def metric_tile(fb, x, y, w, h, theme, icon_name, label, value, sub=None, color=None):
    color = color or theme["accent"]
    fb.panel(x, y, w, h, theme["panel"], border=theme["border"], shadow=theme["shadow"],
             radius=2, inner_top=mix(theme["panel"], theme["fg"], 0.08))
    icon(fb, x + 4, y + 5, icon_name, theme)
    fb.text(x + 15, y + 3, label[:9], theme["muted"], font=FONT3x5)
    fb.text(x + 15, y + 11, value, color, font=FONT5x7)
    if sub:
        fb.text(x + 4, y + h - 8, sub[:14], theme["dim"], font=FONT3x5)
    return w


def panel_title(fb, x, y, w, title, theme, icon_name=None):
    fb.hline(x, y + 7, w, theme["grid"])
    off = 0
    if icon_name:
        icon(fb, x, y, icon_name, theme)
        off = 11
    tw = fb.text(x + off, y + 1, title, theme["muted"], font=FONT3x5)
    fb.rect(x + off - 1, y, tw + 2, 7, theme["bg"])
    fb.text(x + off, y + 1, title, theme["muted"], font=FONT3x5)


def bar_chart(fb, x, y, w, h, values, theme, color=None, highlight_last=8):
    """Столбики недельных коммитов. Возвращает max-значение."""
    color = color or theme["accent"]
    fb.rect(x, y, w, h, theme["panel"])
    for gy in range(0, h, 4):
        fb.hline(x, y + gy, w, theme["grid"])
    if not values:
        fb.text_center(x + w // 2, y + h // 2 - 3, "NO DATA", theme["dim"], font=FONT3x5)
        return 0
    n = len(values)
    bw = max(1, w // n)
    gap = 1 if bw > 2 else 0
    top = max(values) or 1
    for i, v in enumerate(values):
        bx = x + i * bw
        bh = int(round((h - 1) * (v / top)))
        c = color if i >= n - highlight_last else mix(color, theme["panel"], 0.45)
        if bh:
            fb.rect(bx, y + h - bh, bw - gap, bh, c)
            fb.hline(bx, y + h - bh, bw - gap, shade(c, 0.3))
    fb.hline(x, y + h, w, theme["border"])
    return top


def sparkline(fb, x, y, w, h, values, theme, color=None):
    color = color or theme["good"]
    if not values:
        return
    n = min(len(values), w)
    vals = values[-n:]
    top = max(vals) or 1
    prev = None
    for i, v in enumerate(vals):
        px = x + int(i * (w - 1) / max(1, n - 1))
        py = y + h - 1 - int((h - 1) * v / top)
        if prev:
            fb.line(prev[0], prev[1], px, py, color)
        prev = (px, py)
    fb.px(prev[0], prev[1], theme["star"])


def lang_stack(fb, x, y, w, h, languages, theme):
    """Горизонтальная полоса языков + легенда под ней."""
    if not languages:
        fb.rect(x, y, w, h, theme["grid"])
        fb.text(x + 3, y + 1, "NO LANGUAGE DATA", theme["dim"], font=FONT3x5)
        return
    cursor = x
    items = list(languages.items())
    for i, (name, pct) in enumerate(items):
        seg = int(round(w * pct / 100.0)) if i < len(items) - 1 else (x + w - cursor)
        seg = max(1, min(seg, x + w - cursor))
        fb.rect(cursor, y, seg, h, lang_color(name, theme))
        cursor += seg
    fb.frame(x - 1, y - 1, w + 2, h + 2, theme["border"])
    lx = x
    for name, pct in items[:4]:
        fb.rect(lx, y + h + 3, 4, 4, lang_color(name, theme))
        label = "%s %d%%" % (name[:9].upper(), round(pct))
        fb.text(lx + 6, y + h + 3, label, theme["muted"], font=FONT3x5)
        lx += 6 + text_width(label, FONT3x5) + 7


def health_grade(fb, x, y, theme, score, grade):
    colors = {"S": theme["star"], "A": theme["good"], "B": theme["good"],
              "C": theme["warn"], "D": theme["bad"], "E": theme["bad"]}
    c = colors.get(grade, theme["accent"])
    fb.panel(x, y, 22, 24, theme["panel2"], border=c, shadow=theme["shadow"], radius=2)
    fb.text_center(x + 11, y + 4, grade, c, font=FONT5x7, scale=2)
    fb.text_center(x + 11, y + 19, "%d" % score, theme["muted"], font=FONT3x5)
    return c


def owl_frame(name_list, tick, period=10):
    return name_list[(tick // period) % len(name_list)]


def marquee(text, offset, width_chars):
    """Бегущая строка по символам."""
    pad = "   *   "
    s = text + pad
    off = offset % len(s)
    doubled = s + s
    return doubled[off:off + width_chars]
