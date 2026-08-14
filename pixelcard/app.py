"""PixelCard - пиксельный дашборд метрик GitHub на tkinter.

Каждый кадр рисуется в собственный фреймбуфер (pixelcard/fb.py) и заливается
в tk.PhotoImage, затем масштабируется методом zoom - никаких внешних
библиотек и никаких растровых ассетов.
"""
from __future__ import annotations

import argparse
import os
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser

from . import screens
from .ghclient import GitHubClient, GitHubError, demo_card, human
from .state import POMO_BREAK, POMO_WORK, State

FPS = 15


class PixelCardApp:
    def __init__(self, root, st: State, client: GitHubClient):
        self.root = root
        self.st = st
        self.client = client
        self.jobs = queue.Queue()
        self.hex_cache = {}
        self.base_img = None
        self.zoomed = None
        self.last_frame_ms = 0.0
        self._last_time = time.time()
        self._last_buf = None
        self.fps = FPS
        self.debug = False

        root.title("PixelCard - GitHub metrics in pixels")
        root.configure(bg="#000000")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=screens.W * st.scale, height=screens.H * st.scale,
                                highlightthickness=0, bd=0, bg="#000000")
        self.canvas.pack()
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")
        self._make_images()
        self._bind()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.focus_set()
        root.focus_set()
        self.refresh_all()
        self.loop()

    # ------------------------------------------------------------ картинки
    def _make_images(self):
        self.base_img = tk.PhotoImage(width=screens.W, height=screens.H)
        self.canvas.config(width=screens.W * self.st.scale, height=screens.H * self.st.scale)

    def blit(self, fb):
        if fb.buf == self._last_buf:  # кадр не изменился - не тратим CPU
            return False
        self._last_buf = list(fb.buf)
        self.base_img.put(fb.to_tk_data(self.hex_cache), to=(0, 0))
        s = self.st.scale
        self.zoomed = self.base_img.zoom(s, s) if s > 1 else self.base_img
        self.canvas.itemconfig(self.image_id, image=self.zoomed)
        return True

    # -------------------------------------------------------------- клавиши
    def _bind(self):
        r = self.root
        r.bind("<Key>", self.on_key)
        r.bind("<Up>", lambda e: self.nav(-1))
        r.bind("<Down>", lambda e: self.nav(1))
        r.bind("<Return>", self.on_enter)
        r.bind("<BackSpace>", self.on_backspace)
        r.bind("<Escape>", lambda e: self.set_mode("dash"))

    def nav(self, delta):
        st = self.st
        if st.mode == "input" and st.search_results:
            st.search_index = (st.search_index + delta) % len(st.search_results)
            return
        if st.mode != "dash":
            return
        st.move(delta)
        if st.current_repo not in st.cards:
            self.fetch(st.current_repo)

    def on_backspace(self, _event=None):
        if self.st.mode == "input":
            self.st.input_buf = self.st.input_buf[:-1]
        return "break"

    def on_enter(self, _event=None):
        st = self.st
        if st.mode == "input":
            self.commit_input()
        else:
            self.fetch(st.current_repo, force=True)
        return "break"

    def on_key(self, event):
        st = self.st
        ch = event.char
        key = event.keysym.lower()
        if st.mode == "input":
            if ch and ch.isprintable() and len(st.input_buf) < 60:
                st.input_buf += ch
            return "break"

        if key in ("w",):
            return self.nav(-1)
        if key in ("s",):
            return self.nav(1)
        if key.isdigit() and key != "0":
            i = int(key) - 1
            if i < len(st.repos):
                st.index = i
                if st.current_repo not in st.cards:
                    self.fetch(st.current_repo)
            return "break"

        if st.mode == "focus":
            if key == "space":
                st.pomo["running"] = not st.pomo["running"]
                st.toast("focus " + ("started" if st.pomo["running"] else "paused"), "ok")
                return "break"
            if key == "n":
                self.next_phase(manual=True)
                return "break"
            if key == "x":
                st.pomo.update(remaining=POMO_WORK, length=POMO_WORK, mode="work", running=False)
                st.toast("timer reset", "warn")
                return "break"

        if ch == "R" or (key == "r" and event.state & 0x1):
            self.refresh_all(force=True)
        elif key == "r":
            self.fetch(st.current_repo, force=True)
        elif ch == "T":
            st.toast("theme: " + st.next_theme(-1), "ok")
        elif key == "t":
            st.toast("theme: " + st.next_theme(1), "ok")
        elif key == "a":
            self.open_input("add")
        elif key == "f":
            self.open_input("search")
        elif key == "p":
            self.set_mode("dash" if st.mode == "focus" else "focus")
        elif key == "g":
            self.set_mode("dash" if st.mode == "gallery" else "gallery")
        elif key == "h":
            self.set_mode("dash" if st.mode == "help" else "help")
        elif key == "d":
            st.offline = not st.offline
            self.client.offline = st.offline
            st.cards.clear()
            self.refresh_all(force=True)
            st.toast("mode: " + ("demo (offline)" if st.offline else "live github"), "warn")
        elif key == "c":
            repo = st.current_repo
            if repo:
                cmd = "git clone https://github.com/%s.git" % repo
                self.root.clipboard_clear()
                self.root.clipboard_append(cmd)
                st.toast("copied: " + cmd, "ok")
        elif key == "o":
            repo = st.current_repo
            if repo:
                webbrowser.open("https://github.com/" + repo)
                st.toast("opened in browser", "ok")
        elif key == "delete":
            self.remove_repo()
        elif key in ("plus", "equal", "kp_add"):
            self.set_scale(st.scale + 1)
        elif key in ("minus", "kp_subtract"):
            self.set_scale(st.scale - 1)
        elif key == "q":
            self.quit()
        return "break"

    def on_click(self, event):
        st = self.st
        if st.mode != "dash":
            return
        x, y = event.x // st.scale, event.y // st.scale
        if screens.SIDEBAR_X <= x <= screens.SIDEBAR_X + screens.SIDEBAR_W and y > screens.CONTENT_Y + 17:
            row = (y - (screens.CONTENT_Y + 17)) // 17
            visible = (screens.CONTENT_H - 40) // 17
            start = max(0, min(st.index - visible // 2, max(0, len(st.repos) - visible)))
            i = start + row
            if 0 <= i < len(st.repos):
                st.index = i
                if st.current_repo not in st.cards:
                    self.fetch(st.current_repo)

    def set_scale(self, scale):
        self.st.scale = max(2, min(6, scale))
        self._last_buf = None
        self.canvas.config(width=screens.W * self.st.scale, height=screens.H * self.st.scale)
        self.st.toast("pixel scale %dx" % self.st.scale, "ok")

    def set_mode(self, mode):
        self.st.mode = mode
        self.st.search_results = []

    # ----------------------------------------------------------------- ввод
    def open_input(self, kind):
        self.st.mode = "input"
        self.st.input_mode = kind
        self.st.input_buf = ""
        self.st.search_results = []
        self.st.search_index = 0

    def commit_input(self):
        st = self.st
        if st.input_mode == "add":
            name = st.input_buf.strip().strip("/")
            if name.count("/") == 1:
                if name not in st.repos:
                    st.repos.append(name)
                st.index = st.repos.index(name)
                st.mode = "dash"
                st.save()
                self.fetch(name, force=True)
            else:
                st.toast("формат owner/repo", "err")
            return
        if st.search_results:
            name = st.search_results[st.search_index][0]
            if name not in st.repos:
                st.repos.append(name)
            st.index = st.repos.index(name)
            st.mode = "dash"
            st.save()
            self.fetch(name, force=True)
        else:
            self.search(st.input_buf.strip())

    def remove_repo(self):
        st = self.st
        if len(st.repos) <= 1:
            st.toast("нужен хотя бы один репозиторий", "err")
            return
        name = st.repos.pop(st.index)
        st.cards.pop(name, None)
        st.index = min(st.index, len(st.repos) - 1)
        st.save()
        st.toast("removed " + name, "warn")

    # ------------------------------------------------------------- загрузка
    def fetch(self, repo, force=False):
        if not repo:
            return
        if self.st.offline:
            self.st.cards[repo] = demo_card(repo)
            return
        self.st.loading = True
        threading.Thread(target=self._fetch_worker, args=(repo, force), daemon=True).start()

    def _fetch_worker(self, repo, force):
        try:
            card = self.client.repo_card(repo, ttl=0 if force else None)
            self.jobs.put(("card", repo, card, None))
        except GitHubError as exc:
            self.jobs.put(("card", repo, demo_card(repo), str(exc)))
        except Exception as exc:  # noqa: BLE001 - в UI важнее не падать
            self.jobs.put(("card", repo, demo_card(repo), repr(exc)))

    def search(self, query):
        if not query:
            return
        if self.st.offline:
            self.st.search_results = [(query.lower().replace(" ", "-") + "/demo", 1234)]
            return
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()
        self.st.toast("searching github...", "info")

    def _search_worker(self, query):
        try:
            self.jobs.put(("search", query, self.client.search_repos(query), None))
        except Exception as exc:  # noqa: BLE001
            self.jobs.put(("search", query, [], str(exc)))

    def refresh_all(self, force=False):
        for repo in self.st.repos:
            if force or repo not in self.st.cards:
                self.fetch(repo, force=force)

    def drain_jobs(self):
        st = self.st
        while True:
            try:
                kind, key, payload, err = self.jobs.get_nowait()
            except queue.Empty:
                break
            if kind == "card":
                st.cards[key] = payload
                if err:
                    st.toast("%s: %s -> demo" % (key.split("/")[-1], err), "warn")
                elif key == st.current_repo:
                    st.toast("%s loaded - %s stars" % (key.split("/")[-1], human(payload.stars)), "ok")
            elif kind == "search":
                st.search_results = payload
                st.search_index = 0
                if err:
                    st.toast("search failed: " + err, "err")
                elif not payload:
                    st.toast("ничего не найдено", "warn")
        st.loading = any(r not in st.cards for r in st.repos) and not st.offline
        if self.client.rate_remaining is not None:
            st.rate_text = "API %d/%d" % (self.client.rate_remaining, self.client.rate_limit or 0)

    # ------------------------------------------------------------- помодоро
    def next_phase(self, manual=False):
        p = self.st.pomo
        if p["mode"] == "work":
            if not manual:
                p["done"] += 1
                p["minutes"] += POMO_WORK // 60
            p.update(mode="break", remaining=POMO_BREAK, length=POMO_BREAK)
            self.st.toast("перерыв 5 минут, разомни глаза", "ok")
        else:
            p.update(mode="work", remaining=POMO_WORK, length=POMO_WORK)
            self.st.toast("новый focus-блок 25 минут", "ok")
        self.st.save()

    def update_pomo(self, dt):
        p = self.st.pomo
        if not p["running"]:
            return
        p["remaining"] -= dt
        if p["remaining"] <= 0:
            self.next_phase()

    # ----------------------------------------------------------------- цикл
    def loop(self):
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        st = self.st
        st.tick += 1
        if st.tick % 2 == 0:
            st.marquee_offset += 1
        if st.tick % (self.fps * 8) == 0:
            st.tip_index += 1
        st.expire_toast()
        self.drain_jobs()
        self.update_pomo(dt)
        t0 = time.perf_counter()
        self.blit(screens.render(st))
        self.last_frame_ms = (time.perf_counter() - t0) * 1000
        if self.debug:
            self.root.title("PixelCard - %.0f ms/frame, scale %dx" % (self.last_frame_ms, st.scale))
        delay = max(5, int(1000 / self.fps - self.last_frame_ms))
        self.root.after(delay, self.loop)

    def quit(self):
        self.st.save()
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pixelcard", description="PixelCard - GitHub metrics, полностью из пикселей")
    parser.add_argument("repos", nargs="*", help="owner/repo для отслеживания")
    parser.add_argument("--scale", type=int, default=None, help="масштаб пикселя (2-6)")
    parser.add_argument("--offline", action="store_true", help="demo-данные без сети")
    parser.add_argument("--theme", default=None, help="имя темы, например SYNTHWAVE")
    parser.add_argument("--token", default=None, help="GitHub token (иначе $GITHUB_TOKEN)")
    parser.add_argument("--fps", type=int, default=FPS, help="частота кадров (по умолчанию %d)" % FPS)
    parser.add_argument("--debug", action="store_true", help="время кадра в заголовке окна")
    args = parser.parse_args(argv)

    st = State.load(offline=args.offline, scale=args.scale)
    if args.repos:
        st.repos = args.repos
        st.index = 0
    if args.theme:
        from .themes import theme_index
        st.theme_i = theme_index(args.theme.upper(), st.theme_i)
    client = GitHubClient(token=args.token, offline=st.offline)
    if not client.token and not st.offline:
        st.toast("нет GITHUB_TOKEN: лимит 60 req/h", "warn", seconds=8)

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Не удалось открыть окно (%s). Нужен графический дисплей." % exc, file=sys.stderr)
        return 2
    app = PixelCardApp(root, st, client)
    app.fps = max(2, min(60, args.fps))
    app.debug = args.debug
    root.protocol("WM_DELETE_WINDOW", app.quit)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
