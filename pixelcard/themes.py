"""Пиксельные темы. Каждая тема - палитра ролей, спрайты берут цвета отсюда."""
from __future__ import annotations


class Theme:
    def __init__(self, name, **colors):
        self.name = name
        self.colors = colors

    def __getitem__(self, key):
        return self.colors[key]

    def get(self, key, default=None):
        return self.colors.get(key, default)

    def __getattr__(self, item):
        try:
            return self.colors[item]
        except KeyError:
            raise AttributeError(item)


THEMES = [
    Theme(
        "MIDNIGHT OWL",
        bg="#0d1117", bg2="#010409", panel="#161b22", panel2="#21262d",
        border="#30363d", shadow="#010409", grid="#1c2430",
        fg="#f0f6fc", muted="#8b949e", dim="#484f58",
        accent="#58a6ff", accent2="#bc8cff", good="#3fb950",
        warn="#d29922", bad="#f85149", star="#ffd33d",
        owl_body="#7d5ba6", owl_body2="#5b4180", owl_belly="#e8d7ff",
        owl_beak="#ffb457", owl_eye="#0d1117",
    ),
    Theme(
        "GAMEBOY DMG",
        bg="#9bbc0f", bg2="#8bac0f", panel="#8bac0f", panel2="#9bbc0f",
        border="#0f380f", shadow="#306230", grid="#306230",
        fg="#0f380f", muted="#306230", dim="#306230",
        accent="#0f380f", accent2="#306230", good="#0f380f",
        warn="#306230", bad="#0f380f", star="#0f380f",
        owl_body="#306230", owl_body2="#0f380f", owl_belly="#9bbc0f",
        owl_beak="#0f380f", owl_eye="#0f380f",
    ),
    Theme(
        "SYNTHWAVE",
        bg="#160e28", bg2="#0b0616", panel="#241640", panel2="#33205c",
        border="#ff4fd8", shadow="#0b0616", grid="#3b2470",
        fg="#fdf6ff", muted="#b39ddb", dim="#6c4ea3",
        accent="#00e5ff", accent2="#ff4fd8", good="#00ffa3",
        warn="#ffcc00", bad="#ff3b6b", star="#ffe066",
        owl_body="#ff4fd8", owl_body2="#a3208f", owl_belly="#ffe9fb",
        owl_beak="#ffcc00", owl_eye="#160e28",
    ),
    Theme(
        "FOREST TERMINAL",
        bg="#0b1a12", bg2="#050d08", panel="#132a1d", panel2="#1c3b28",
        border="#2f6b45", shadow="#050d08", grid="#1a3324",
        fg="#d9f2e3", muted="#7fb391", dim="#4a7a5c",
        accent="#4ade80", accent2="#a3e635", good="#22c55e",
        warn="#facc15", bad="#ef4444", star="#fde047",
        owl_body="#8b6f47", owl_body2="#5d4a2f", owl_belly="#e7d7b8",
        owl_beak="#facc15", owl_eye="#0b1a12",
    ),
    Theme(
        "PAPER ZINE",
        bg="#f4efe4", bg2="#e5ddcb", panel="#fffdf7", panel2="#efe7d6",
        border="#2b2b2b", shadow="#c9c0ad", grid="#ded4c0",
        fg="#1f1f1f", muted="#6b6459", dim="#a49b8c",
        accent="#1d6fd6", accent2="#c2410c", good="#177245",
        warn="#b45309", bad="#b91c1c", star="#e0a500",
        owl_body="#8d6e4f", owl_body2="#5f4a34", owl_belly="#f8ecd8",
        owl_beak="#e0a500", owl_eye="#1f1f1f",
    ),
    Theme(
        "C64 BLUE",
        bg="#40318d", bg2="#302472", panel="#7869c4", panel2="#8f82d8",
        border="#0a0a3c", shadow="#241a5c", grid="#5a4bab",
        fg="#ffffff", muted="#cfc7ff", dim="#9a8ce0",
        accent="#6cf0ff", accent2="#ff77a8", good="#7ce07c",
        warn="#ffe27a", bad="#ff6b6b", star="#ffe27a",
        owl_body="#ffe27a", owl_body2="#c9a94f", owl_belly="#fffdf0",
        owl_beak="#ff77a8", owl_eye="#0a0a3c",
    ),
    Theme(
        "SOLAR FLARE",
        bg="#1b1207", bg2="#0d0904", panel="#2e1d0c", panel2="#412a13",
        border="#e07a1f", shadow="#0d0904", grid="#3b2712",
        fg="#ffeccc", muted="#c99a63", dim="#8a663d",
        accent="#ff9f1c", accent2="#ffbf69", good="#94d82d",
        warn="#ffd166", bad="#ef476f", star="#ffd166",
        owl_body="#e07a1f", owl_body2="#a0510c", owl_belly="#ffeccc",
        owl_beak="#ffd166", owl_eye="#1b1207",
    ),
    Theme(
        "ICE CAVE",
        bg="#0a1620", bg2="#050c12", panel="#12283a", panel2="#1b3b52",
        border="#3d7ea6", shadow="#050c12", grid="#17334a",
        fg="#e6f4ff", muted="#8fbcd9", dim="#4f7f9e",
        accent="#5ec8f7", accent2="#a5f3fc", good="#34d399",
        warn="#fbbf24", bad="#fb7185", star="#e0f2fe",
        owl_body="#8fbcd9", owl_body2="#5b8bab", owl_belly="#f2fbff",
        owl_beak="#fbbf24", owl_eye="#0a1620",
    ),
]

THEMES_BY_NAME = {t.name: t for t in THEMES}


def theme_index(name, default=0):
    for i, t in enumerate(THEMES):
        if t.name == name:
            return i
    return default
