"""Тесты PixelCard: рендер, шрифты, спрайты, метрики, конфиг."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelcard import screens
from pixelcard.fb import Framebuffer, mix, rgb, shade
from pixelcard.ghclient import GitHubClient, GitHubError, RepoCard, days_ago, demo_card, human
from pixelcard.pixelfont import BIG_DIGITS, FONT3x5, FONT5x7, text_width
from pixelcard.sprites import SPRITES, resolve_palette
from pixelcard.state import State
from pixelcard.themes import THEMES
from pixelcard.widgets import LANG_COLORS, identicon, marquee


class TestFramebuffer(unittest.TestCase):
    def test_rgb_forms(self):
        self.assertEqual(rgb("#ff0000"), 0xFF0000)
        self.assertEqual(rgb("#f00"), 0xFF0000)
        self.assertEqual(rgb(0x123456), 0x123456)

    def test_clipping(self):
        fb = Framebuffer(10, 10, "#000000")
        fb.px(-5, -5, "#ffffff")
        fb.px(50, 50, "#ffffff")
        fb.rect(-4, -4, 100, 100, "#ff0000")
        self.assertEqual(fb.get(0, 0), 0xFF0000)
        self.assertEqual(fb.get(9, 9), 0xFF0000)

    def test_shapes(self):
        fb = Framebuffer(20, 20, "#000000")
        fb.hline(2, 3, 5, "#00ff00")
        self.assertEqual(fb.get(2, 3), 0x00FF00)
        self.assertEqual(fb.get(7, 3), 0x000000)
        fb.frame(0, 0, 20, 20, "#0000ff")
        self.assertEqual(fb.get(0, 10), 0x0000FF)
        self.assertEqual(fb.get(10, 10), 0x000000)
        fb.line(0, 0, 19, 19, "#ffffff")
        self.assertEqual(fb.get(10, 10), 0xFFFFFF)

    def test_mix_shade(self):
        self.assertEqual(mix("#000000", "#ffffff", 1.0), 0xFFFFFF)
        self.assertEqual(mix("#000000", "#ffffff", 0.0), 0x000000)
        self.assertGreater(shade("#808080", 0.5), 0x808080)
        self.assertLess(shade("#808080", -0.5), 0x808080)

    def test_tk_data_shape(self):
        fb = Framebuffer(3, 2, "#010203")
        data = fb.to_tk_data()
        self.assertEqual(data.count("{"), 2)
        self.assertEqual(data.count("#010203"), 6)

    def test_png_export(self):
        fb = Framebuffer(8, 8, "#123456")
        with tempfile.TemporaryDirectory() as tmp:
            path = fb.to_png(os.path.join(tmp, "a.png"), scale=3)
            with open(path, "rb") as fh:
                head = fh.read(8)
            self.assertEqual(head, b"\x89PNG\r\n\x1a\n")
            self.assertGreater(os.path.getsize(path), 50)


class TestFonts(unittest.TestCase):
    def test_glyph_geometry(self):
        for font, w, h in ((FONT5x7, 5, 7), (FONT3x5, 3, 5), (BIG_DIGITS, 7, 9)):
            for ch, glyph in font.items():
                self.assertEqual(len(glyph), h, ch)
                self.assertTrue(all(len(r) == w for r in glyph), ch)
                self.assertTrue(set("".join(glyph)) <= {"#", "."}, ch)

    def test_coverage(self):
        need = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,:;-_+=/()[]%#@!?"
        for ch in need:
            self.assertIn(ch, FONT5x7, ch)

    def test_cyrillic_coverage(self):
        cyr = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        for ch in cyr:
            self.assertIn(ch, FONT5x7, ch)
            self.assertIn(ch, FONT3x5, ch)
            self.assertIn(ch.lower().upper(), FONT5x7, ch)

    def test_ui_text_has_no_missing_glyphs(self):
        """Всё, что мы рисуем в интерфейсе, должно иметь глифы (иначе '?')."""
        from pixelcard.ghclient import DEV_TIPS
        from pixelcard.screens import KEYS
        from pixelcard.themes import THEMES as _T
        texts = [t for t in DEV_TIPS] + [k for k, _ in KEYS] + [v for _, v in KEYS] \
            + [th.name for th in _T]
        for text in texts:
            for ch in text.upper():
                self.assertIn(ch, FONT5x7, "нет глифа %r в %r" % (ch, text))

    def test_text_width_and_draw(self):
        self.assertEqual(text_width("AB", FONT5x7), 11)
        fb = Framebuffer(40, 12, "#000000")
        used = fb.text(1, 1, "HI", "#ffffff")
        self.assertEqual(used, text_width("HI", FONT5x7))
        self.assertNotEqual(sum(fb.buf), 0)

    def test_unknown_char_fallback(self):
        fb = Framebuffer(30, 12, "#000000")
        fb.text(0, 0, "Ω≈", "#ffffff")  # не должно падать


class TestSprites(unittest.TestCase):
    def test_rectangular(self):
        for name, rows in SPRITES.items():
            widths = {len(r) for r in rows}
            self.assertEqual(len(widths), 1, name)
            self.assertGreaterEqual(len(rows), 5, name)

    def test_count(self):
        self.assertGreaterEqual(len(SPRITES), 60)

    def test_palette_resolves_all_chars(self):
        pal = resolve_palette(THEMES[0])
        for name, rows in SPRITES.items():
            chars = set("".join(rows)) - {".", " "}
            missing = chars - set(pal)
            self.assertFalse(missing, "%s: %s" % (name, missing))

    def test_owls_symmetric(self):
        for name in ("owl_idle", "owl_blink", "owl_sleep", "owl_big"):
            for row in SPRITES[name]:
                self.assertEqual(row, row[::-1], name)


class TestThemes(unittest.TestCase):
    def test_same_roles_everywhere(self):
        roles = set(THEMES[0].colors)
        self.assertGreaterEqual(len(THEMES), 6)
        for th in THEMES:
            self.assertEqual(set(th.colors), roles, th.name)
            for role in roles:
                rgb(th[role])


class TestMetrics(unittest.TestCase):
    def test_human(self):
        self.assertEqual(human(999), "999")
        self.assertEqual(human(1234), "1.2K")
        self.assertEqual(human(15400), "15K")
        self.assertEqual(human(2_500_000), "2.5M")
        self.assertEqual(human(None), "-")

    def test_days_ago(self):
        self.assertEqual(days_ago(""), 9999)
        self.assertEqual(days_ago("garbage"), 9999)
        self.assertGreater(days_ago("2000-01-01T00:00:00Z"), 8000)

    def test_health_bounds_and_order(self):
        weak = RepoCard("a/b", pushed_at="2005-01-01T00:00:00Z")
        strong = demo_card("python/cpython")
        ws, wg = weak.health()
        ss, sg = strong.health()
        self.assertTrue(0 <= ws <= 100 and 0 <= ss <= 100)
        self.assertGreater(ss, ws)
        self.assertIn(wg, "SABCDE")

    def test_issues_only_never_negative(self):
        card = RepoCard("a/b", open_issues=3, open_prs=10)
        self.assertEqual(card.issues_only, 0)

    def test_demo_card_is_deterministic(self):
        a, b = demo_card("foo/bar"), demo_card("foo/bar")
        self.assertEqual((a.stars, a.forks, a.weekly_commits), (b.stars, b.forks, b.weekly_commits))
        self.assertEqual(len(a.weekly_commits), 52)
        self.assertTrue(a.demo)

    def test_offline_client_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = GitHubClient(cache_dir=tmp, offline=True)
            with self.assertRaises(GitHubError):
                client.repo_card("python/cpython")
            with self.assertRaises(GitHubError):
                client.repo_card("not-a-repo")

    def test_cache_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = GitHubClient(cache_dir=tmp)
            client._cache_write("/x", {"a": 1}, {"h": "v"})
            data, headers = client.get("/x")
            self.assertEqual(data, {"a": 1})
            self.assertEqual(headers, {"h": "v"})

    def test_link_header_parsing(self):
        headers = {"link": '<https://api.github.com/x?page=2>; rel="next", '
                           '<https://api.github.com/x?page=42>; rel="last"'}
        self.assertEqual(GitHubClient._last_page(headers), 42)
        self.assertIsNone(GitHubClient._last_page({}))


class TestState(unittest.TestCase):
    def test_navigation_wraps(self):
        st = State(repos=["a/b", "c/d"])
        st.move(1)
        self.assertEqual(st.current_repo, "c/d")
        st.move(1)
        self.assertEqual(st.current_repo, "a/b")
        st.move(-1)
        self.assertEqual(st.current_repo, "c/d")

    def test_theme_cycle(self):
        st = State()
        first = st.theme.name
        for _ in range(len(THEMES)):
            st.next_theme(1)
        self.assertEqual(st.theme.name, first)

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            st = State(repos=["x/y", "z/w"], theme_i=2)
            st.index = 1
            st.pomo["done"] = 4
            self.assertTrue(st.save(path))
            back = State.load(path)
            self.assertEqual(back.repos, ["x/y", "z/w"])
            self.assertEqual(back.theme.name, THEMES[2].name)
            self.assertEqual(back.index, 1)
            self.assertEqual(back.pomo["done"], 4)

    def test_load_missing_file_uses_defaults(self):
        st = State.load(os.path.join(tempfile.gettempdir(), "nope-pixelcard.json"))
        self.assertTrue(st.repos)

    def test_toast_expires(self):
        st = State()
        st.toast("hello", "ok", seconds=-1)
        st.expire_toast()
        self.assertEqual(st.status, "")


class TestWidgets(unittest.TestCase):
    def test_identicon_deterministic(self):
        a, b = Framebuffer(20, 20), Framebuffer(20, 20)
        identicon(a, 2, 2, "python/cpython", THEMES[0])
        identicon(b, 2, 2, "python/cpython", THEMES[0])
        self.assertEqual(a.buf, b.buf)
        c = Framebuffer(20, 20)
        identicon(c, 2, 2, "torvalds/linux", THEMES[0])
        self.assertNotEqual(a.buf, c.buf)

    def test_marquee_length_and_cycle(self):
        text = "TIP: keep it simple"
        self.assertEqual(len(marquee(text, 0, 20)), 20)
        self.assertEqual(marquee(text, 0, 10), marquee(text, len(text + "   *   "), 10))

    def test_lang_colors_are_valid(self):
        for name, color in LANG_COLORS.items():
            rgb(color)


class TestScreens(unittest.TestCase):
    def _state(self, mode, theme_i=0):
        st = State(theme_i=theme_i, offline=True)
        for repo in st.repos:
            st.cards[repo] = demo_card(repo)
        st.mode = mode
        return st

    def test_all_modes_render(self):
        for mode in screens.SCREENS:
            fb = screens.render(self._state(mode))
            self.assertEqual((fb.w, fb.h), (screens.W, screens.H))
            self.assertGreater(len(set(fb.buf)), 8, mode)

    def test_all_themes_render(self):
        for i, th in enumerate(THEMES):
            fb = screens.render(self._state("dash", i))
            self.assertGreater(len(set(fb.buf)), 8, th.name)

    def test_render_without_cards(self):
        st = State(offline=True)
        fb = screens.render(st)  # данные не загружены - не должно падать
        self.assertEqual(fb.w, screens.W)

    def test_render_with_empty_metrics(self):
        st = State(repos=["a/b"], offline=True)
        st.cards["a/b"] = RepoCard("a/b")
        screens.render(st)

    def test_render_is_reasonably_fast(self):
        import time
        st = self._state("dash")
        t0 = time.perf_counter()
        for _ in range(5):
            screens.render(st)
        avg = (time.perf_counter() - t0) / 5
        self.assertLess(avg, 0.25, "кадр рисуется слишком долго: %.3fs" % avg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
