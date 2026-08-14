"""Экраны PixelCard. Каждая функция рисует кадр в Framebuffer."""
from __future__ import annotations

import time

from .fb import Framebuffer, mix, shade
from .ghclient import DEV_TIPS, human
from .pixelfont import BIG_DIGITS, FONT3x5, FONT5x7, text_width
from .sprites import OWL_ANIM, SPRITES
from .widgets import (badge, bar_chart, button, health_grade, icon, identicon,
                      lang_stack, marquee, metric_tile, progress, sparkline)

W, H = 384, 248
HEADER_H = 24
FOOTER_Y = 222
CONTENT_Y = 26
CONTENT_H = FOOTER_Y - CONTENT_Y - 4
SIDEBAR_X, SIDEBAR_W = 4, 104
MAIN_X = 112
MAIN_W = W - MAIN_X - 4

KEYS = [
    ("UP/DN", "REPO"), ("R", "RELOAD"), ("T", "THEME"), ("A", "ADD"),
    ("F", "FIND"), ("P", "FOCUS"), ("G", "SPRITES"), ("C", "CLONE"),
    ("O", "OPEN"), ("H", "HELP"),
]


def new_frame(theme):
    fb = Framebuffer(W, H, theme["bg"])
    fb.dots(0, 0, W, H, theme["grid"], step=8)
    return fb


# ------------------------------------------------------------------- шапка
def draw_header(fb, st):
    th = st.theme
    fb.gradient_v(0, 0, W, HEADER_H, th["bg2"], th["panel"])
    fb.scanlines(0, 0, W, HEADER_H, mix(th["bg2"], th["bg"], 0.5), step=3)
    fb.hline(0, HEADER_H - 1, W, th["border"])
    frame = OWL_ANIM[(st.tick // 6) % len(OWL_ANIM)]
    icon(fb, 5, 4, frame, th)
    fb.text(26, 3, "PIXELCARD", th["accent"], font=FONT5x7, scale=2, shadow=th["shadow"])
    fb.text(26, 18, "GITHUB METRICS FOR PIXEL PEOPLE", th["dim"], font=FONT3x5)

    x = W - 4
    clock = time.strftime("%H:%M:%S")
    x -= text_width(clock, FONT3x5) + 2
    fb.text(x, 4, clock, th["fg"], font=FONT3x5)
    icon(fb, x - 10, 2, "clock", th)
    live = "DEMO" if st.offline else "LIVE"
    lw = text_width(live, FONT3x5) + 6
    fb.panel(W - 4 - lw, 13, lw, 9, th["warn"] if st.offline else th["good"], radius=1)
    fb.text(W - 1 - lw, 15, live, th["bg"], font=FONT3x5)
    rate = st.rate_text or ("CACHE" if st.offline else "API OK")
    fb.text_right(W - 8 - lw, 15, rate, th["muted"], font=FONT3x5)
    tname = st.theme.name
    fb.text_right(x - 14, 4, tname, th["accent2"], font=FONT3x5)
    icon(fb, x - 14 - text_width(tname, FONT3x5) - 10, 2, "palette", th)


# ------------------------------------------------------------------ подвал
def draw_footer(fb, st):
    th = st.theme
    fb.rect(0, FOOTER_Y, W, H - FOOTER_Y, th["panel"])
    fb.hline(0, FOOTER_Y, W, th["border"])
    x = 4
    for key, label in KEYS:
        w = text_width("[%s]" % key, FONT3x5) + text_width(label, FONT3x5) + 11
        button(fb, x, FOOTER_Y + 3, w, 11, key, label, th,
               active=(st.mode == "focus" and key == "P") or (st.mode == "gallery" and key == "G"))
        x += w + 2
    tip = DEV_TIPS[st.tip_index % len(DEV_TIPS)]
    icon(fb, 4, FOOTER_Y + 17, "bulb", th)
    line = marquee("TIP: " + tip, st.marquee_offset, 118)
    fb.text(15, FOOTER_Y + 19, line, th["muted"], font=FONT3x5)
    if st.status:
        kind = {"ok": th["good"], "err": th["bad"], "warn": th["warn"]}.get(st.status_kind, th["accent"])
        sw = text_width(st.status[:44], FONT3x5) + 8
        fb.panel(W - sw - 4, FOOTER_Y + 16, sw, 11, kind, radius=1)
        fb.text(W - sw, FOOTER_Y + 19, st.status[:44], th["bg"], font=FONT3x5)


# ---------------------------------------------------------------- сайдбар
def draw_sidebar(fb, st):
    th = st.theme
    fb.panel(SIDEBAR_X, CONTENT_Y, SIDEBAR_W, CONTENT_H, th["panel"],
             border=th["border"], shadow=th["shadow"], radius=2,
             inner_top=mix(th["panel"], th["fg"], 0.08))
    icon(fb, SIDEBAR_X + 4, CONTENT_Y + 4, "folder", th)
    fb.text(SIDEBAR_X + 15, CONTENT_Y + 5, "TRACKED REPOS", th["fg"], font=FONT3x5)
    fb.hline(SIDEBAR_X + 3, CONTENT_Y + 13, SIDEBAR_W - 6, th["grid"])

    y = CONTENT_Y + 17
    row_h = 17
    visible = (CONTENT_H - 40) // row_h
    start = max(0, min(st.index - visible // 2, max(0, len(st.repos) - visible)))
    for i in range(start, min(len(st.repos), start + visible)):
        name = st.repos[i]
        card = st.cards.get(name)
        sel = (i == st.index)
        if sel:
            fb.panel(SIDEBAR_X + 2, y - 1, SIDEBAR_W - 4, row_h - 1,
                     mix(th["panel2"], th["accent"], 0.25), border=th["accent"], radius=1)
        identicon(fb, SIDEBAR_X + 5, y + 2, name, th, scale=2, size=5)
        short = name.split("/")[-1][:13].upper()
        fb.text(SIDEBAR_X + 18, y + 1, short, th["fg"] if sel else th["muted"], font=FONT3x5)
        if card:
            icon(fb, SIDEBAR_X + 17, y + 7, "star_small", th)
            fb.text(SIDEBAR_X + 24, y + 8, human(card.stars), th["star"], font=FONT3x5)
            spark = card.weekly_commits[-16:]
            if spark:
                sparkline(fb, SIDEBAR_X + 58, y + 7, 40, 7, spark, th,
                          color=th["good"] if sel else th["dim"])
        else:
            fb.text(SIDEBAR_X + 18, y + 8, "..." if st.loading else "PRESS R", th["dim"], font=FONT3x5)
        y += row_h

    total = sum(c.stars for c in st.cards.values() if c)
    by = CONTENT_Y + CONTENT_H - 20
    fb.hline(SIDEBAR_X + 3, by - 3, SIDEBAR_W - 6, th["grid"])
    icon(fb, SIDEBAR_X + 4, by, "star", th)
    fb.text(SIDEBAR_X + 15, by + 1, "TOTAL " + human(total), th["star"], font=FONT3x5)
    fb.text(SIDEBAR_X + 15, by + 8, "%d REPOS TRACKED" % len(st.repos), th["dim"], font=FONT3x5)


# ------------------------------------------------------------- главный блок
def draw_repo_header(fb, st, card):
    th = st.theme
    x, y, w, h = MAIN_X, CONTENT_Y, MAIN_W, 42
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"],
             radius=2, inner_top=mix(th["panel"], th["fg"], 0.1))
    if not card:
        fb.text(x + 8, y + 12, "NO DATA - PRESS [R] TO LOAD", th["muted"], font=FONT5x7)
        return
    identicon(fb, x + 6, y + 6, card.full_name, th, scale=3, size=5)
    owner, _, repo = card.full_name.partition("/")
    fb.text(x + 27, y + 5, repo[:18].upper(), th["fg"], font=FONT5x7,
            scale=2 if len(repo) <= 12 else 1, shadow=th["shadow"])
    fb.text(x + 27, y + 21, owner[:24].upper(), th["accent"], font=FONT3x5)
    desc = (card.description or "no description").upper()[:46]
    fb.text(x + 27, y + 29, desc, th["muted"], font=FONT3x5)
    bx = x + 27
    for t in card.topics[:3]:
        bx += badge(fb, bx, y + 35, t[:10].upper(), th, bg=th["panel2"], fg=th["accent2"]) + 3
    if card.archived:
        badge(fb, bx, y + 35, "ARCHIVED", th, bg=th["bad"], fg=th["bg"])
    score, grade = card.health()
    c = health_grade(fb, x + w - 28, y + 8, th, score, grade)
    fb.text_right(x + w - 30, y + 5, "HEALTH", th["muted"], font=FONT3x5)
    fb.text_right(x + w - 30, y + 12, ("%s / %s" % (card.language[:8].upper(), card.license[:9].upper())), c,
                  font=FONT3x5)
    upd = "PUSH %sD AGO" % card.days_since_push if card.days_since_push < 9999 else "PUSH ?"
    fb.text_right(x + w - 30, y + 19, upd, th["muted"], font=FONT3x5)
    if card.release_tag:
        fb.text_right(x + w - 30, y + 26, "REL " + card.release_tag[:10].upper(), th["accent2"], font=FONT3x5)
    fb.text_right(x + w - 30, y + 33, "BRANCH " + card.default_branch[:8].upper(), th["dim"], font=FONT3x5)


def draw_tiles(fb, st, card):
    th = st.theme
    tw, gap, tile_h = 64, 4, 30
    rows = [
        [("star", "STARS", human(card.stars if card else 0), th["star"], "GAZERS"),
         ("fork", "FORKS", human(card.forks if card else 0), th["accent"], "COPIES"),
         ("eye", "WATCH", human(card.watchers if card else 0), th["accent2"], "SUBSCRIBED"),
         ("bug", "ISSUES", human(card.issues_only if card else 0), th["bad"], "OPEN NOW")],
        [("pr", "PULLS", human(card.open_prs if card else 0), th["good"], "OPEN PR"),
         ("users", "PEOPLE", human(card.contributors if card else 0), th["accent"], "CONTRIBUTORS"),
         ("commit", "COMMITS", human(card.commits_90d if card else 0), th["good"], "LAST 90 DAYS"),
         ("disk", "SIZE", human((card.size_kb if card else 0) * 1024).replace("K", "KB").replace("M", "MB"),
          th["muted"], "ON DISK")],
    ]
    for r, row in enumerate(rows):
        y = CONTENT_Y + 46 + r * (tile_h + gap)
        for i, (ic, label, value, color, sub) in enumerate(row):
            metric_tile(fb, MAIN_X + i * (tw + gap), y, tw, tile_h, th, ic, label, value, sub, color)


def draw_chart(fb, st, card):
    th = st.theme
    x, y, w, h = MAIN_X, CONTENT_Y + 114, MAIN_W, 46
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"], radius=2)
    icon(fb, x + 4, y + 3, "chart", th)
    fb.text(x + 15, y + 4, "COMMITS PER WEEK / LAST YEAR", th["fg"], font=FONT3x5)
    vals = card.weekly_commits if card else []
    top = bar_chart(fb, x + 4, y + 12, w - 42, h - 20, vals, th, color=th["accent"])
    rx = x + w - 34
    fb.text(rx, y + 12, "MAX", th["dim"], font=FONT3x5)
    fb.text(rx, y + 19, human(top), th["fg"], font=FONT3x5)
    fb.text(rx, y + 27, "YEAR", th["dim"], font=FONT3x5)
    fb.text(rx, y + 34, human(card.commits_year if card else 0), th["good"], font=FONT3x5)


def draw_langs(fb, st, card):
    th = st.theme
    x, y, w, h = MAIN_X, CONTENT_Y + 166, MAIN_W, 26
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"], radius=2)
    icon(fb, x + 4, y + 3, "code", th)
    fb.text(x + 15, y + 4, "LANGUAGE MIX", th["fg"], font=FONT3x5)
    lang_stack(fb, x + 5, y + 12, w - 10, 6, card.languages if card else {}, th)


def draw_dashboard(fb, st):
    card = st.current_card
    draw_header(fb, st)
    draw_sidebar(fb, st)
    draw_repo_header(fb, st, card)
    if card:
        draw_tiles(fb, st, card)
    draw_chart(fb, st, card)
    draw_langs(fb, st, card)
    draw_footer(fb, st)
    if st.loading:
        loading_strip(fb, st)


def loading_strip(fb, st):
    th = st.theme
    n = 20
    x = MAIN_X + MAIN_W // 2 - n * 3 // 2
    y = CONTENT_Y + 100
    fb.panel(x - 6, y - 6, n * 3 + 12, 18, th["panel2"], border=th["accent"], radius=1)
    for i in range(n):
        on = (st.tick // 2 + i) % n < 6
        fb.rect(x + i * 3, y, 2, 6, th["accent"] if on else th["grid"])
    fb.text(x, y + 8, "FETCHING FROM GITHUB", th["muted"], font=FONT3x5)


# ------------------------------------------------------------------- ФОКУС
def draw_focus(fb, st):
    th = st.theme
    p = st.pomo
    draw_header(fb, st)
    x, y, w, h = SIDEBAR_X, CONTENT_Y, W - 8, CONTENT_H
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"], radius=3,
             inner_top=mix(th["panel"], th["fg"], 0.1))
    fb.scanlines(x + 2, y + 2, w - 4, h - 4, mix(th["panel"], th["bg"], 0.4), step=4)

    mode = p["mode"]
    label = "FOCUS SESSION" if mode == "work" else "BREAK TIME"
    fb.text_center(x + w // 2, y + 8, label, th["accent"], font=FONT5x7)
    mins, secs = divmod(max(0, int(p["remaining"])), 60)
    clock = "%02d:%02d" % (mins, secs)
    cw = text_width(clock, BIG_DIGITS) * 3
    color = th["good"] if mode == "work" else th["accent2"]
    if p["running"] and int(p["remaining"]) % 2 == 0:
        color = shade(color, 0.15)
    fb.text((x + w // 2) - cw // 2, y + 24, clock, color, font=BIG_DIGITS, spacing=1, scale=3,
            shadow=th["shadow"])
    total = p["length"]
    ratio = 1.0 - (p["remaining"] / total if total else 0)
    progress(fb, x + 40, y + 62, w - 80, 8, ratio, th, color=color)
    fb.text_center(x + w // 2, y + 74, "%d%% DONE - %s" % (round(ratio * 100),
                   "RUNNING" if p["running"] else "PAUSED"), th["muted"], font=FONT3x5)

    owl = "owl_happy" if p["running"] and mode == "work" else "owl_sleep"
    fb.sprite(x + 12, y + h - 62, SPRITES[owl if mode == "work" else "owl_sleep"],
              _pal(th), scale=2)
    if not p["running"]:
        fb.text(x + 62, y + h - 56, "Z", th["muted"], font=FONT5x7)
        fb.text(x + 70, y + h - 62, "Z", th["dim"], font=FONT3x5)

    dots_x = x + w // 2 - 4 * 12
    for i in range(8):
        done = i < p["done"] % 8 or (p["done"] >= 8 and p["done"] % 8 == 0)
        c = th["good"] if done else th["grid"]
        fb.sprite(dots_x + i * 12, y + 86, SPRITES["tomato"], _pal(th, {"r": c, "G": th["good"] if done else th["dim"]}))
    fb.text_center(x + w // 2, y + 98, "POMODOROS TODAY: %d   FOCUS MINUTES: %d"
                   % (p["done"], p["minutes"]), th["fg"], font=FONT3x5)

    card = st.current_card
    if card:
        fb.hline(x + 30, y + 112, w - 60, th["grid"])
        fb.text_center(x + w // 2, y + 118, "WORKING ON: " + card.full_name.upper()[:40],
                       th["accent2"], font=FONT3x5)
        fb.text_center(x + w // 2, y + 126, "%s STARS  %s OPEN ISSUES  %s COMMITS/90D"
                       % (human(card.stars), human(card.issues_only), human(card.commits_90d)),
                       th["muted"], font=FONT3x5)
    tips = DEV_TIPS[(st.tip_index) % len(DEV_TIPS)]
    fb.text_center(x + w // 2, y + h - 24, ("TIP: " + tips).upper()[:82], th["dim"], font=FONT3x5)
    fb.text_center(x + w // 2, y + h - 14, "[SPACE] START/PAUSE  [N] NEXT PHASE  [X] RESET  [P] BACK",
                   th["muted"], font=FONT3x5)
    draw_footer(fb, st)


def _pal(theme, extra=None):
    from .sprites import resolve_palette
    return resolve_palette(theme, extra)


# ---------------------------------------------------------------- ГАЛЕРЕЯ
def draw_gallery(fb, st):
    th = st.theme
    draw_header(fb, st)
    x, y, w, h = SIDEBAR_X, CONTENT_Y, W - 8, CONTENT_H
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"], radius=3)
    fb.text(x + 6, y + 5, "SPRITE ATLAS - %d SPRITES, ALL HAND-PIXELED" % len(SPRITES),
            th["fg"], font=FONT3x5)
    fb.hline(x + 4, y + 13, w - 8, th["grid"])

    names = [n for n in SPRITES if not n.startswith("owl")]
    cols, cell_w, cell_h = 12, 30, 26
    for i, name in enumerate(names):
        cx = x + 6 + (i % cols) * cell_w
        cy = y + 18 + (i // cols) * cell_h
        if cy + cell_h > y + h - 46:
            break
        fb.panel(cx, cy, cell_w - 3, cell_h - 3, th["panel2"], radius=1)
        sw = len(SPRITES[name][0])
        fb.sprite(cx + (cell_w - 3 - sw * 2) // 2, cy + 2, SPRITES[name], _pal(th), scale=2)
        fb.text(cx + 1, cy + cell_h - 9, name[:9].upper(), th["muted"], font=FONT3x5)

    oy = y + h - 44
    fb.hline(x + 4, oy - 4, w - 8, th["grid"])
    for i, owl in enumerate(["owl_idle", "owl_blink", "owl_wink", "owl_happy", "owl_wings", "owl_sleep"]):
        fb.sprite(x + 8 + i * 36, oy, SPRITES[owl], _pal(th), scale=2)
        fb.text(x + 8 + i * 36, oy + 34, owl.replace("owl_", "").upper(), th["dim"], font=FONT3x5)
    fb.sprite(x + w - 60, oy - 4, SPRITES["owl_big"], _pal(th), scale=2)
    px = x + 236
    fb.text(px, oy, "THEME PALETTE: " + th.name, th["fg"], font=FONT3x5)
    for i, role in enumerate(["accent", "accent2", "good", "warn", "bad", "star",
                              "fg", "muted", "panel2", "border"]):
        fb.rect(px + (i % 5) * 14, oy + 9 + (i // 5) * 14, 12, 12, th[role])
        fb.frame(px + (i % 5) * 14, oy + 9 + (i // 5) * 14, 12, 12, th["border"])
    draw_footer(fb, st)


# ------------------------------------------------------------------- ПОМОЩЬ
def draw_help(fb, st):
    th = st.theme
    draw_header(fb, st)
    x, y, w, h = SIDEBAR_X, CONTENT_Y, W - 8, CONTENT_H
    fb.panel(x, y, w, h, th["panel"], border=th["border"], shadow=th["shadow"], radius=3)
    fb.sprite(x + 8, y + 6, SPRITES["owl_big"], _pal(th), scale=2)
    fb.text(x + 62, y + 8, "PIXELCARD MANUAL", th["accent"], font=FONT5x7, scale=2, shadow=th["shadow"])
    fb.text(x + 62, y + 26, "GITHUB DASHBOARD RENDERED PIXEL BY PIXEL: NO IMAGES, NO FONTS,", th["muted"], font=FONT3x5)
    fb.text(x + 62, y + 34, "ONLY PYTHON + TKINTER FRAMEBUFFER.", th["muted"], font=FONT3x5)
    fb.text(x + 62, y + 44, "68 СПРАЙТОВ / 8 ТЕМ / 3 ПИКСЕЛЬНЫХ ШРИФТА / 0 ЗАВИСИМОСТЕЙ", th["accent2"], font=FONT3x5)
    rows = [
        ("UP/DOWN W/S", "выбрать репозиторий"),
        ("ENTER / R", "обновить активный репо"),
        ("SHIFT+R", "обновить все репозитории"),
        ("A", "добавить репо owner/name"),
        ("F", "поиск репо на github"),
        ("DELETE", "убрать репо из списка"),
        ("T / SHIFT+T", "следующая / прошлая тема"),
        ("P", "фокус: помодоро 25/5"),
        ("SPACE N X", "старт-пауза / фаза / сброс"),
        ("G", "атлас спрайтов и палитра"),
        ("C", "git clone в буфер обмена"),
        ("O", "открыть репо в браузере"),
        ("D", "demo / live данные"),
        ("1 - 9", "быстрый переход к репо"),
        ("+ / -", "масштаб пикселя 2x - 6x"),
        ("H / ESC", "справка / назад"),
        ("Q", "выход с сохранением"),
    ]
    col_y = y + 60
    for i, (k, v) in enumerate(rows):
        cx = x + 6 + (i % 2) * 190
        cy = col_y + (i // 2) * 11
        fb.panel(cx, cy, 56, 9, th["panel2"], radius=1)
        fb.text(cx + 3, cy + 2, k[:13], th["accent"], font=FONT3x5)
        fb.text(cx + 60, cy + 2, v[:28], th["fg"], font=FONT3x5)
    fy = y + h - 26
    fb.hline(x + 6, fy - 4, w - 12, th["grid"])
    fb.text(x + 10, fy, "TOKEN: export GITHUB_TOKEN=ghp_xxx  ->  5000 req/h вместо 60", th["muted"], font=FONT3x5)
    fb.text(x + 10, fy + 9, "CONFIG: ~/.pixelcard/config.json   CACHE: ~/.pixelcard/cache", th["dim"], font=FONT3x5)
    draw_footer(fb, st)


# ------------------------------------------------------------------- ВВОД
def draw_input(fb, st):
    draw_dashboard(fb, st)
    th = st.theme
    fb.scanlines(0, HEADER_H, W, FOOTER_Y - HEADER_H, th["bg2"], step=2)
    w, h = 260, 92
    x, y = (W - w) // 2, 70
    fb.panel(x, y, w, h, th["panel"], border=th["accent"], shadow=th["shadow"], radius=2,
             inner_top=mix(th["panel"], th["fg"], 0.12))
    title = "ADD REPOSITORY" if st.input_mode == "add" else "SEARCH GITHUB"
    icon(fb, x + 6, y + 5, "plus" if st.input_mode == "add" else "search", th)
    fb.text(x + 18, y + 6, title, th["accent"], font=FONT3x5)
    hint = "OWNER/NAME, THEN ENTER" if st.input_mode == "add" else "TYPE QUERY, ENTER TO SEARCH"
    fb.text(x + 18, y + 14, hint, th["dim"], font=FONT3x5)
    fb.panel(x + 6, y + 24, w - 12, 14, th["bg"], border=th["border"], radius=1)
    text = st.input_buf[-38:]
    fb.text(x + 10, y + 28, text, th["fg"], font=FONT5x7)
    if (st.tick // 6) % 2 == 0:
        fb.rect(x + 10 + text_width(text, FONT5x7) + 1, y + 27, 4, 8, th["accent"])
    ry = y + 44
    if st.search_results:
        for i, (name, stars) in enumerate(st.search_results[:5]):
            sel = i == st.search_index
            if sel:
                fb.panel(x + 6, ry - 1, w - 12, 9, mix(th["panel2"], th["accent"], 0.3), radius=1)
            fb.text(x + 9, ry + 1, name[:34].upper(), th["fg"] if sel else th["muted"], font=FONT3x5)
            fb.text_right(x + w - 9, ry + 1, human(stars), th["star"], font=FONT3x5)
            ry += 10
        fb.text(x + 6, y + h - 10, "UP/DOWN CHOOSE - ENTER ADD - ESC CANCEL", th["dim"], font=FONT3x5)
    else:
        fb.text(x + 6, y + h - 10, "ENTER CONFIRM - ESC CANCEL", th["dim"], font=FONT3x5)


SCREENS = {
    "dash": draw_dashboard,
    "focus": draw_focus,
    "gallery": draw_gallery,
    "help": draw_help,
    "input": draw_input,
}


def render(st):
    fb = new_frame(st.theme)
    SCREENS.get(st.mode, draw_dashboard)(fb, st)
    return fb
