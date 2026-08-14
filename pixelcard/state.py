"""Состояние приложения. Отделено от tkinter, чтобы экраны можно было
рендерить в PNG в тестах."""
from __future__ import annotations

import json
import os

from .themes import THEMES, theme_index

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".pixelcard")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_REPOS = [
    "python/cpython",
    "torvalds/linux",
    "microsoft/vscode",
    "rust-lang/rust",
    "pallets/flask",
    "tqdm/tqdm",
    "psf/requests",
    "astral-sh/ruff",
]

POMO_WORK = 25 * 60
POMO_BREAK = 5 * 60


class State:
    def __init__(self, repos=None, theme_i=0, offline=False, scale=3):
        self.repos = list(repos or DEFAULT_REPOS)
        self.index = 0
        self.cards = {}
        self.theme_i = theme_i % len(THEMES)
        self.offline = offline
        self.scale = scale
        self.mode = "dash"
        self.prev_mode = "dash"
        self.tick = 0
        self.marquee_offset = 0
        self.tip_index = 0
        self.status = ""
        self.status_kind = "info"
        self.status_until = 0.0
        self.loading = False
        self.rate_text = ""
        self.input_buf = ""
        self.input_mode = "add"
        self.search_results = []
        self.search_index = 0
        self.pomo = {"mode": "work", "running": False, "remaining": POMO_WORK,
                     "length": POMO_WORK, "done": 0, "minutes": 0}

    # --- удобные свойства -------------------------------------------------
    @property
    def theme(self):
        return THEMES[self.theme_i % len(THEMES)]

    @property
    def current_repo(self):
        if not self.repos:
            return None
        self.index = max(0, min(self.index, len(self.repos) - 1))
        return self.repos[self.index]

    @property
    def current_card(self):
        repo = self.current_repo
        return self.cards.get(repo) if repo else None

    # --- конфиг -----------------------------------------------------------
    def to_config(self):
        return {"repos": self.repos, "theme": self.theme.name, "index": self.index,
                "scale": self.scale, "offline": self.offline,
                "pomodoros": self.pomo["done"], "focus_minutes": self.pomo["minutes"]}

    def save(self, path=CONFIG_PATH):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                json.dump(self.to_config(), fh, indent=2)
            return True
        except OSError:
            return False

    @classmethod
    def load(cls, path=CONFIG_PATH, offline=False, scale=None):
        cfg = {}
        try:
            with open(path) as fh:
                cfg = json.load(fh)
        except (OSError, ValueError):
            pass
        st = cls(repos=cfg.get("repos") or None,
                 theme_i=theme_index(cfg.get("theme", ""), 0),
                 offline=offline or bool(cfg.get("offline")),
                 scale=scale or cfg.get("scale", 3))
        st.index = min(cfg.get("index", 0), max(0, len(st.repos) - 1))
        st.pomo["done"] = cfg.get("pomodoros", 0)
        st.pomo["minutes"] = cfg.get("focus_minutes", 0)
        return st

    # --- действия ---------------------------------------------------------
    def toast(self, text, kind="info", seconds=3.5):
        import time
        self.status = text.upper()
        self.status_kind = kind
        self.status_until = time.time() + seconds

    def expire_toast(self):
        import time
        if self.status and time.time() > self.status_until:
            self.status = ""

    def move(self, delta):
        if self.repos:
            self.index = (self.index + delta) % len(self.repos)

    def next_theme(self, delta=1):
        self.theme_i = (self.theme_i + delta) % len(THEMES)
        return self.theme.name
