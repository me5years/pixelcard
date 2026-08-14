"""Рендер всех экранов в PNG без tkinter - для проверки вёрстки."""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelcard import screens
from pixelcard.ghclient import demo_card
from pixelcard.state import State
from pixelcard.themes import THEMES


def build_state(theme_i=0, mode="dash"):
    st = State(theme_i=theme_i, offline=True)
    for r in st.repos:
        st.cards[r] = demo_card(r)
    st.mode = mode
    st.tick = 12
    st.rate_text = "API 4832/5000"
    st.toast("cpython loaded - 126K stars", "ok", seconds=999)
    return st


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    made = []
    for mode in ("dash", "focus", "gallery", "help", "input"):
        st = build_state(0, mode)
        if mode == "input":
            st.input_mode = "search"
            st.input_buf = "pixel art"
            st.search_results = [("okgreece/pixel-art", 1200), ("nostalgic-css/NES.css", 21000),
                                 ("Kirlovon/PixelArt", 340), ("jvalen/pixel-art-react", 6100),
                                 ("aseprite/aseprite", 26000)]
        if mode == "focus":
            st.pomo.update(running=True, remaining=754, done=3, minutes=75)
        t0 = time.perf_counter()
        fb = screens.render(st)
        dt = (time.perf_counter() - t0) * 1000
        path = os.path.join(outdir, "screen_%s.png" % mode)
        fb.to_png(path, scale=2)
        made.append((path, dt))
    for i, th in enumerate(THEMES):
        st = build_state(i, "dash")
        path = os.path.join(outdir, "theme_%02d_%s.png" % (i, th.name.split()[0].lower()))
        screens.render(st).to_png(path, scale=2)
        made.append((path, 0))
    for path, dt in made:
        print("%-42s %s" % (os.path.basename(path), ("%.1f ms" % dt) if dt else ""))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preview")
