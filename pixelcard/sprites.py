"""Спрайтовая библиотека PixelCard.

Формат: строки-«арт». Символы -> роли палитры (см. THEME_CHARS) либо
локальная палитра спрайта. '.' и ' ' - прозрачно.

Роли из темы: K=border, F=fg, M=muted, D=dim, A=accent, B=accent2,
G=good, W=warn, R=bad, S=star, P=panel, Q=panel2, o/d/b/y/e = сова.
"""
from __future__ import annotations

THEME_CHARS = {
    "K": "border", "F": "fg", "M": "muted", "D": "dim",
    "A": "accent", "B": "accent2", "G": "good", "W": "warn",
    "R": "bad", "S": "star", "P": "panel", "Q": "panel2",
    "o": "owl_body", "d": "owl_body2", "b": "owl_belly",
    "y": "owl_beak", "e": "owl_eye",
}

LITERAL_CHARS = {
    "w": "#ffffff", "k": "#000000", "g": "#9e9e9e", "r": "#ff5555",
    "n": "#2b2b2b", "c": "#7fdbff", "m": "#ff77c8", "l": "#c0f070",
    "t": "#a0642c", "s": "#ffd166", "u": "#6a5acd", "p": "#f78166",
}


def resolve_palette(theme, extra=None):
    pal = {ch: theme[role] for ch, role in THEME_CHARS.items()}
    pal.update(LITERAL_CHARS)
    if extra:
        pal.update(extra)
    return pal


def _s(*rows):
    """Нормализует спрайт: все строки одной ширины."""
    w = max(len(r) for r in rows)
    return tuple(r.ljust(w, ".") for r in rows)


# ---------------------------------------------------------------- СОВЫ 16x16
def _mir(*halves):
    """Собирает симметричный спрайт: левая половина + её зеркало."""
    return tuple(h + h[::-1] for h in halves)


OWL_IDLE = _mir(
    "...dd...", "..dood..", "..dooooo", ".doooooo", "dooooooo",
    "dowwwwwo", "doweewwo", "dowwwwwo", "dooooooy", ".doooooy",
    ".dooobbb", "..dobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)

OWL_BLINK = _mir(
    "...dd...", "..dood..", "..dooooo", ".doooooo", "dooooooo",
    "doooooooo"[:8], "doeeeeeo", "dooooooo", "dooooooy", ".doooooy",
    ".dooobbb", "..dobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)

OWL_WINK = _mir(
    "...dd...", "..dood..", "..dooooo", ".doooooo", "dooooooo",
    "dowwwwwo", "doweewwo", "dowwwwwo", "dooooooy", ".doooooy",
    ".dooobbb", "..dobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)
OWL_WINK = tuple(
    row if i not in (5, 6, 7) else row[:8] + ("ooooooood"[:8] if i != 6 else "oeeeeeod")
    for i, row in enumerate(OWL_WINK)
)

OWL_HAPPY = _mir(
    "...dd...", "..dood..", "..dooooo", ".doooooo", "dooooooo",
    "doweooeo", "dowewewo", "dowweewo", "dooooooy", ".doooooy",
    ".dooobbb", "..dobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)

OWL_WINGS_UP = _mir(
    "d..dd...", "dd.dood.", "ddodoooo", ".doooooo", "dooooooo",
    "dowwwwwo", "doweewwo", "dowwwwwo", "dooooooy", "ddoooooy",
    "ddoobbbb", ".ddobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)

OWL_SLEEP = _mir(
    "...dd...", "..dood..", "..dooooo", ".doooooo", "dooooooo",
    "dooooooo", "doeeeeeo", "dooooooo", "dooooooy", ".doooooy",
    ".dooobbb", "..dobbbb", "..dobbbb", "...ddobb", "....dooo", "....yyy.",
)

OWL_BIG = _mir(
    "....dd......", "...dood.....", "...dood.....", "..dooooddddd",
    ".doooooooooo", "dooooooooooo", "dooooooooooo", "doowwwwwwwoo",
    "doowweeewwoo", "doowweeewwoo", "doowwwwwwwoo", "dooooooooooy",
    ".dooooooooyy", ".dooooooooyy", "..dooooooooy", "..dooooobbbb",
    "...doobbbbbb", "...dobbbbbbb", "....dobbbbbb", "....dobbbbbb",
    ".....ddobbbb", "......ddoobb", ".......dddoo", "....yyy.yy..",
)

# ------------------------------------------------------------- ИКОНКИ 8x8/9x9
STAR = _s(
    "...SS...",
    "...SS...",
    ".SSSSSS.",
    "SSSSSSSS",
    ".SSSSSS.",
    "..SSSS..",
    ".SS..SS.",
    "SS....SS",
)

STAR_SMALL = _s(
    "..S..",
    ".SSS.",
    "SSSSS",
    ".SSS.",
    "S...S",
)

FORK = _s(
    "AA...AA.",
    "AA...AA.",
    "AA...AA.",
    "AAAAAAA.",
    "...AA...",
    "...AA...",
    "..AAAA..",
    "..AAAA..",
)

EYE = _s(
    "........",
    "..FFFF..",
    ".F....F.",
    "F..FF..F",
    "F..FF..F",
    ".F....F.",
    "..FFFF..",
    "........",
)

BUG = _s(
    "R..RR..R",
    ".RRRRRR.",
    "RRRRRRRR",
    "R.RRRR.R",
    "RRRRRRRR",
    "R.RRRR.R",
    ".RRRRRR.",
    "R..RR..R",
)

BRANCH = _s(
    ".GG..GG.",
    ".GG..GG.",
    ".GG..GG.",
    ".GGGGGG.",
    "...GG...",
    "..GGGG..",
    "..GGGG..",
    "...GG...",
)

COMMIT = _s(
    "...AA...",
    "...AA...",
    ".AAAAAA.",
    "AA.AA.AA",
    "AA.AA.AA",
    ".AAAAAA.",
    "...AA...",
    "...AA...",
)

PULL_REQUEST = _s(
    "BB....BB",
    "BB....BB",
    "BB..BBBB",
    "BB..BB..",
    "BBBBBB..",
    "..BB....",
    ".BBBB...",
    ".BBBB...",
)

ISSUE = _s(
    "..GGGG..",
    ".G....G.",
    "G..GG..G",
    "G.GGGG.G",
    "G.GGGG.G",
    "G..GG..G",
    ".G....G.",
    "..GGGG..",
)

CLOCK = _s(
    "..FFFF..",
    ".F.F..F.",
    "F..F...F",
    "F..FFF.F",
    "F......F",
    "F......F",
    ".F....F.",
    "..FFFF..",
)

TOMATO = _s(
    "...GG...",
    "..GGGG..",
    ".rrrrrr.",
    "rrrwrrrr",
    "rrrwrrrr",
    "rrrrrrrr",
    ".rrrrrr.",
    "..rrrr..",
)

COFFEE = _s(
    "...MM...",
    "..M..M..",
    "tttttt..",
    "ttwwtttF",
    "ttttttFF",
    "ttttttF.",
    ".tttt...",
    "..tt....",
)

TERMINAL = _s(
    "KKKKKKKK",
    "K......K",
    "K.GG...K",
    "K..GG..K",
    "K.GG...K",
    "K..GGG.K",
    "K......K",
    "KKKKKKKK",
)

KEYBOARD = _s(
    "KKKKKKKK",
    "KFKFKFKK",
    "KKKKKKKK",
    "KFKFKFKK",
    "KKKKKKKK",
    "KFFFFFKK",
    "KKKKKKKK",
    "........",
)

ROCKET = _s(
    "...ww...",
    "..wRRw..",
    "..wRRw..",
    "..wwww..",
    ".wwwwww.",
    "w.wwww.w",
    "...WW...",
    "...W....",
)

HEART = _s(
    ".RR..RR.",
    "RRRRRRRR",
    "RRRRRRRR",
    "RRRRRRRR",
    ".RRRRRR.",
    "..RRRR..",
    "...RR...",
    "........",
)

LOCK = _s(
    "..WWWW..",
    ".W....W.",
    ".W....W.",
    "WWWWWWWW",
    "WWW..WWW",
    "WWW..WWW",
    "WWWWWWWW",
    "........",
)

KEY = _s(
    "..SSS...",
    ".S...S..",
    ".S...S..",
    "..SSS...",
    "...S....",
    "...SS...",
    "...S....",
    "...SS...",
)

FOLDER = _s(
    "SSSS....",
    "SSSSSSS.",
    "SSSSSSSS",
    "SSSSSSSS",
    "SSSSSSSS",
    "SSSSSSSS",
    "SSSSSSSS",
    "........",
)

FILE_CODE = _s(
    "FFFFF...",
    "FFFFFF..",
    "FF...FF.",
    "FF.A.AF.",
    "FFA...AF",
    "FF.A.AF.",
    "FFFFFFF.",
    "........",
)

CLOUD = _s(
    "...MMM..",
    "..MMMMM.",
    ".MMMMMMM",
    "MMMMMMMM",
    "MMMMMMMM",
    ".MMMMMM.",
    "........",
    "........",
)

DATABASE = _s(
    ".AAAAAA.",
    "A......A",
    ".AAAAAA.",
    "A......A",
    ".AAAAAA.",
    "A......A",
    ".AAAAAA.",
    "........",
)

GEAR = _s(
    "..M..M..",
    "MMMMMMMM",
    ".MMMMMM.",
    "MMM..MMM",
    "MMM..MMM",
    ".MMMMMM.",
    "MMMMMMMM",
    "..M..M..",
)

FLAME = _s(
    "...W....",
    "..WW....",
    "..WWW...",
    ".WWSWW..",
    "WWSSSWW.",
    "WSSSSSW.",
    ".WSSSW..",
    "..WWW...",
)

TROPHY = _s(
    "SSSSSSSS",
    "SSSSSSSS",
    ".SSSSSS.",
    "..SSSS..",
    "...SS...",
    "..SSSS..",
    ".SSSSSS.",
    "........",
)

BELL = _s(
    "...WW...",
    "..WWWW..",
    ".WWWWWW.",
    ".WWWWWW.",
    "WWWWWWWW",
    "WWWWWWWW",
    "...WW...",
    "........",
)

MOON = _s(
    "..FFFF..",
    ".FF..FF.",
    "FF....F.",
    "FF......",
    "FF......",
    "FF....F.",
    ".FF..FF.",
    "..FFFF..",
)

SUN = _s(
    "S..S..S.",
    ".SSSSS..",
    ".SSSSS..",
    "SSSSSSS.",
    ".SSSSS..",
    ".SSSSS..",
    "S..S..S.",
    "........",
)

PYTHON = _s(
    ".AAAA...",
    ".A..A...",
    ".AAAAGG.",
    "...A..G.",
    ".G..A...",
    ".GGGGG..",
    "...G..G.",
    "...GGGG.",
)

CAT = _s(
    "M..MM..M",
    "MMMMMMMM",
    "MFMMMMFM",
    "MMMMMMMM",
    "MMFFFFMM",
    "MMMMMMMM",
    ".MMMMMM.",
    "..M..M..",
)

CURSOR = _s(
    "F.......",
    "FF......",
    "FFF.....",
    "FFFF....",
    "FFFFF...",
    "FFF.....",
    "F..F....",
    "....F...",
)

CHECK = _s(
    "......GG",
    ".....GG.",
    "....GG..",
    "G..GG...",
    "GG.GG...",
    ".GGG....",
    "..G.....",
    "........",
)

CROSS = _s(
    "R......R",
    "RR....RR",
    ".RR..RR.",
    "..RRRR..",
    "..RRRR..",
    ".RR..RR.",
    "RR....RR",
    "R......R",
)

ARROW_UP = _s("...FF...", "..FFFF..", ".FFFFFF.", "FFFFFFFF", "...FF...", "...FF...", "...FF...", "........")
ARROW_DOWN = _s("...FF...", "...FF...", "...FF...", "FFFFFFFF", ".FFFFFF.", "..FFFF..", "...FF...", "........")
ARROW_LEFT = _s("...F....", "..FF....", ".FFFFFFF", "FFFFFFFF", ".FFFFFFF", "..FF....", "...F....", "........")
ARROW_RIGHT = _s("....F...", "....FF..", "FFFFFFF.", "FFFFFFFF", "FFFFFFF.", "....FF..", "....F...", "........")

PLUS = _s("...FF...", "...FF...", "...FF...", "FFFFFFFF", "FFFFFFFF", "...FF...", "...FF...", "...FF...")
REFRESH = _s(
    "..AAAA..",
    ".A....A.",
    "A....AAA",
    "A.....A.",
    "A.......",
    "A....A.A",
    ".A...AAA",
    "..AAAA..",
)
PALETTE_ICON = _s(
    "..BBBB..",
    ".BAABBB.",
    "BAAGGRBB",
    "BAGGRRSB",
    "BGGRRSSB",
    "BGRRSSSB",
    ".BRSSSB.",
    "..BBBB..",
)
CHART = _s(
    "........",
    "..A...A.",
    "..A.A.A.",
    "A.A.A.A.",
    "A.A.A.A.",
    "A.A.A.A.",
    "A.A.A.A.",
    "KKKKKKKK",
)
GEM = _s(
    ".cccccc.",
    "cwwccccc",
    "cwcccccc",
    ".cccccc.",
    "..cccc..",
    "...cc...",
    "........",
    "........",
)
BULB = _s(
    "..SSSS..",
    ".SSSSSS.",
    ".SSwwSS.",
    ".SSSSSS.",
    "..SSSS..",
    "...MM...",
    "...MM...",
    "........",
)
WIFI = _s(
    "..AAAA..",
    ".A....A.",
    "A..AA..A",
    "..A..A..",
    "...AA...",
    "........",
    "...AA...",
    "...AA...",
)
BATTERY = _s(
    "........",
    "KKKKKKK.",
    "KGGGG.KK",
    "KGGGG.KK",
    "KGGGG.KK",
    "KKKKKKK.",
    "........",
    "........",
)
DISK = _s(
    "KKKKKKKK",
    "K.FFFF.K",
    "K.FFFF.K",
    "K.FFFF.K",
    "KKKKKKKK",
    "KFFFFFFK",
    "KFFFFFFK",
    "KKKKKKKK",
)
GHOST = _s(
    "..wwww..",
    ".wwwwww.",
    "wwkwwkww",
    "wwkwwkww",
    "wwwwwwww",
    "wwwwwwww",
    "wwwwwwww",
    "w.ww.ww.",
)
DICE = _s(
    "KKKKKKKK",
    "KFF..FFK",
    "KFF..FFK",
    "K..FF..K",
    "K..FF..K",
    "KFF..FFK",
    "KFF..FFK",
    "KKKKKKKK",
)
MEDAL = _s(
    "S......S",
    "SS....SS",
    ".SS..SS.",
    "..SSSS..",
    ".SwwwwS.",
    "SwwSSwwS",
    ".SwwwwS.",
    "..SSSS..",
)
TAG = _s(
    ".BBBBBB.",
    "BB....BB",
    "B.wB...B",
    "B..B...B",
    "B...B..B",
    "B....B.B",
    "BB....BB",
    ".BBBBBB.",
)
SCROLL = _s(
    ".FFFFFF.",
    "F......F",
    "F.MMMM.F",
    "F.MMMM.F",
    "F.MMMM.F",
    "F.MMM..F",
    "F......F",
    ".FFFFFF.",
)
USERS = _s(
    ".AA.AA..",
    ".AA.AA..",
    "AAAAAAA.",
    "AAAAAAA.",
    "AAAAAAA.",
    "AA...AA.",
    "........",
    "........",
)
CALENDAR = _s(
    ".F..F...",
    "FFFFFFF.",
    "FFFFFFF.",
    "F.....F.",
    "F.FF..F.",
    "F.....F.",
    "FFFFFFF.",
    "........",
)
CODE_TAG = _s(
    "........",
    "..A..A..",
    ".A....A.",
    "A..BB..A",
    "A.BB...A",
    ".A....A.",
    "..A..A..",
    "........",
)
SEARCH = _s(
    ".FFFF...",
    "F....F..",
    "F....F..",
    "F....F..",
    ".FFFF...",
    "...FFF..",
    "....FFF.",
    ".....FF.",
)
WARNING = _s(
    "...WW...",
    "...WW...",
    "..WWWW..",
    "..WkkWW.",
    ".WWkkWW.",
    ".WWkkWWW",
    "WWWWWWWW",
    "WWWWWWWW",
)
DOWNLOAD = _s(
    "...GG...",
    "...GG...",
    "...GG...",
    "GG.GG.GG",
    ".GGGGGG.",
    "..GGGG..",
    "...GG...",
    "GGGGGGGG",
)
CUBE = _s(
    "..BBBB..",
    ".BBBBBB.",
    "BBBBBBBB",
    "BB.BB.BB",
    "BB.BB.BB",
    ".BBBBBB.",
    "..BBBB..",
    "........",
)
SNAKE_LOGO = _s(
    ".AAAA...",
    "A....A..",
    "A.wA.A..",
    "A....A..",
    "AAAAAAGG",
    "..A....G",
    "..GGGGGG",
    "....GG..",
)
LEAF = _s(
    ".....GG.",
    "...GGGG.",
    "..GGGGG.",
    ".GGGGGG.",
    "GGGGGGG.",
    "GGGGG...",
    ".GG.....",
    "G.......",
)
SHIELD = _s(
    "AAAAAAAA",
    "AwwwwwwA",
    "Aw.GG.wA",
    "AwGGGGwA",
    "AwwGGwwA",
    ".AwwwwA.",
    "..AwwA..",
    "...AA...",
)

SPRITES = {
    "owl_idle": OWL_IDLE, "owl_blink": OWL_BLINK, "owl_wink": OWL_WINK,
    "owl_wings": OWL_WINGS_UP, "owl_sleep": OWL_SLEEP, "owl_happy": OWL_HAPPY,
    "owl_big": OWL_BIG,
    "star": STAR, "star_small": STAR_SMALL, "fork": FORK, "eye": EYE,
    "bug": BUG, "branch": BRANCH, "commit": COMMIT, "pr": PULL_REQUEST,
    "issue": ISSUE, "clock": CLOCK, "tomato": TOMATO, "coffee": COFFEE,
    "terminal": TERMINAL, "keyboard": KEYBOARD, "rocket": ROCKET,
    "heart": HEART, "lock": LOCK, "key": KEY, "folder": FOLDER,
    "file": FILE_CODE, "cloud": CLOUD, "database": DATABASE, "gear": GEAR,
    "flame": FLAME, "trophy": TROPHY, "bell": BELL, "moon": MOON, "sun": SUN,
    "python": PYTHON, "cat": CAT, "cursor": CURSOR, "check": CHECK,
    "cross": CROSS, "arrow_up": ARROW_UP, "arrow_down": ARROW_DOWN,
    "arrow_left": ARROW_LEFT, "arrow_right": ARROW_RIGHT, "plus": PLUS,
    "refresh": REFRESH, "palette": PALETTE_ICON, "chart": CHART, "gem": GEM,
    "bulb": BULB, "wifi": WIFI, "battery": BATTERY, "disk": DISK,
    "ghost": GHOST, "dice": DICE, "medal": MEDAL, "tag": TAG,
    "scroll": SCROLL, "users": USERS, "calendar": CALENDAR,
    "code": CODE_TAG, "search": SEARCH, "warning": WARNING,
    "download": DOWNLOAD, "cube": CUBE, "snake": SNAKE_LOGO, "leaf": LEAF,
    "shield": SHIELD,
}

OWL_ANIM = ["owl_idle", "owl_idle", "owl_idle", "owl_blink", "owl_idle",
            "owl_idle", "owl_wings", "owl_idle", "owl_wink", "owl_idle"]


def sprite(name):
    return SPRITES[name]


def sprite_size(name):
    rows = SPRITES[name]
    return len(rows[0]), len(rows)
