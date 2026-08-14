"""Логика приложения без реального tkinter: клавиши, помодоро, загрузка, blit."""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelcard import app as app_module
from pixelcard.ghclient import GitHubClient
from pixelcard.state import POMO_BREAK, POMO_WORK, State


class FakePhotoImage:
    def __init__(self, width=1, height=1):
        self.width_ = width
        self.height_ = height
        self.puts = 0

    def put(self, data, to=None):
        assert isinstance(data, str) and data.startswith("{")
        assert data.count("{") == self.height_, "строк в данных должно быть height"
        self.puts += 1

    def zoom(self, x, y=None):
        return FakePhotoImage(self.width_ * x, self.height_ * (y or x))


class FakeCanvas:
    def __init__(self, *a, **kw):
        self.items = {}
        self.bindings = {}

    def pack(self, **kw):
        pass

    def create_image(self, *a, **kw):
        self.items[1] = kw
        return 1

    def config(self, **kw):
        self.items.setdefault("config", []).append(kw)

    def bind(self, seq, fn):
        self.bindings[seq] = fn

    def focus_set(self):
        pass

    def itemconfig(self, item, **kw):
        self.items[item] = kw


class FakeRoot:
    def __init__(self):
        self.scheduled = []
        self.bindings = {}
        self.clipboard = []
        self.destroyed = False
        self.title_text = ""

    def title(self, text):
        self.title_text = text

    def configure(self, **kw):
        pass

    def resizable(self, *a):
        pass

    def bind(self, seq, fn):
        self.bindings[seq] = fn

    def focus_set(self):
        pass

    def after(self, delay, fn):
        self.scheduled.append((delay, fn))

    def clipboard_clear(self):
        self.clipboard = []

    def clipboard_append(self, text):
        self.clipboard.append(text)

    def protocol(self, *a):
        pass

    def destroy(self):
        self.destroyed = True


def key(ch="", keysym=None, state=0):
    return types.SimpleNamespace(char=ch, keysym=keysym or ch or "??", state=state)


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.fake_tk = types.SimpleNamespace(
            Canvas=lambda *a, **kw: FakeCanvas(),
            PhotoImage=FakePhotoImage,
            Tk=FakeRoot,
            TclError=Exception,
        )
        self._real_tk = app_module.tk
        app_module.tk = self.fake_tk
        self.root = FakeRoot()
        self.st = State(repos=["python/cpython", "torvalds/linux"], offline=True)
        self.client = GitHubClient(offline=True, cache_dir=os.path.join(os.sep, "tmp", "pixelcard-test"))
        self.app = app_module.PixelCardApp(self.root, self.st, self.client)

    def tearDown(self):
        app_module.tk = self._real_tk


class TestStartup(AppTestCase):
    def test_offline_cards_loaded_and_frame_drawn(self):
        self.assertEqual(set(self.st.cards), set(self.st.repos))
        self.assertTrue(self.st.cards["python/cpython"].demo)
        self.assertTrue(self.root.scheduled, "цикл рендера должен быть запланирован")

    def test_blit_skips_identical_frames(self):
        from pixelcard import screens
        self.st.next_theme(1)  # изменили кадр -> должен отрисоваться
        fb = screens.render(self.st)
        self.assertTrue(self.app.blit(fb))
        self.assertFalse(self.app.blit(screens.render(self.st)))


class TestKeys(AppTestCase):
    def test_navigation(self):
        self.app.on_key(key("s"))
        self.assertEqual(self.st.current_repo, "torvalds/linux")
        self.app.on_key(key("w"))
        self.assertEqual(self.st.current_repo, "python/cpython")
        self.app.on_key(key("2"))
        self.assertEqual(self.st.index, 1)

    def test_theme_switch_both_directions(self):
        start = self.st.theme.name
        self.app.on_key(key("t"))
        self.assertNotEqual(self.st.theme.name, start)
        self.app.on_key(key("T", "t", state=0x1))
        self.assertEqual(self.st.theme.name, start)

    def test_modes(self):
        for ch, mode in (("p", "focus"), ("g", "gallery"), ("h", "help")):
            self.app.on_key(key(ch))
            self.assertEqual(self.st.mode, mode)
            self.app.on_key(key(ch))
            self.assertEqual(self.st.mode, "dash")

    def test_clone_to_clipboard(self):
        self.app.on_key(key("c"))
        self.assertEqual(self.root.clipboard, ["git clone https://github.com/python/cpython.git"])

    def test_scale_limits(self):
        for _ in range(10):
            self.app.on_key(key("+", "plus"))
        self.assertEqual(self.st.scale, 6)
        for _ in range(10):
            self.app.on_key(key("-", "minus"))
        self.assertEqual(self.st.scale, 2)

    def test_add_repo_flow(self):
        self.app.on_key(key("a"))
        self.assertEqual(self.st.mode, "input")
        for ch in "octocat/hello-world":
            self.app.on_key(key(ch))
        self.assertEqual(self.st.input_buf, "octocat/hello-world")
        self.app.on_enter()
        self.assertEqual(self.st.mode, "dash")
        self.assertIn("octocat/hello-world", self.st.repos)
        self.assertIn("octocat/hello-world", self.st.cards)

    def test_add_repo_rejects_bad_format(self):
        self.app.on_key(key("a"))
        for ch in "garbage":
            self.app.on_key(key(ch))
        self.app.on_enter()
        self.assertEqual(self.st.mode, "input")
        self.assertIn("OWNER/REPO", self.st.status)

    def test_backspace_in_input(self):
        self.app.on_key(key("a"))
        for ch in "abc":
            self.app.on_key(key(ch))
        self.app.on_backspace()
        self.assertEqual(self.st.input_buf, "ab")

    def test_remove_repo_keeps_at_least_one(self):
        self.app.remove_repo()
        self.assertEqual(len(self.st.repos), 1)
        self.app.remove_repo()
        self.assertEqual(len(self.st.repos), 1)

    def test_search_offline_stub(self):
        self.app.on_key(key("f"))
        for ch in "pixel":
            self.app.on_key(key(ch))
        self.app.on_enter()
        self.assertTrue(self.st.search_results)
        self.app.on_enter()
        self.assertEqual(self.st.mode, "dash")

    def test_quit_saves_and_destroys(self):
        self.app.on_key(key("q"))
        self.assertTrue(self.root.destroyed)


class TestPomodoro(AppTestCase):
    def test_start_pause_and_phases(self):
        self.app.on_key(key("p"))
        self.app.on_key(key(" ", "space"))
        self.assertTrue(self.st.pomo["running"])
        self.app.update_pomo(10)
        self.assertAlmostEqual(self.st.pomo["remaining"], POMO_WORK - 10)
        self.app.update_pomo(POMO_WORK)
        self.assertEqual(self.st.pomo["mode"], "break")
        self.assertEqual(self.st.pomo["length"], POMO_BREAK)
        self.assertEqual(self.st.pomo["done"], 1)
        self.assertEqual(self.st.pomo["minutes"], POMO_WORK // 60)

    def test_reset(self):
        self.app.on_key(key("p"))
        self.st.pomo["remaining"] = 5
        self.app.on_key(key("x"))
        self.assertEqual(self.st.pomo["remaining"], POMO_WORK)
        self.assertFalse(self.st.pomo["running"])

    def test_manual_next_phase_does_not_count(self):
        self.app.on_key(key("p"))
        self.app.on_key(key("n"))
        self.assertEqual(self.st.pomo["mode"], "break")
        self.assertEqual(self.st.pomo["done"], 0)


class TestFetchFallback(AppTestCase):
    def test_live_fetch_without_network_falls_back_to_demo(self):
        self.st.offline = False
        self.client.offline = True   # сеть недоступна -> GitHubError
        self.app.fetch("some/repo", force=True)
        import time
        for _ in range(200):
            self.app.drain_jobs()
            if "some/repo" in self.st.cards:
                break
            time.sleep(0.01)
        self.assertIn("some/repo", self.st.cards)
        self.assertTrue(self.st.cards["some/repo"].demo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
