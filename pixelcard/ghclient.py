"""Клиент GitHub API на stdlib (urllib) + файловый кэш + офлайн demo-режим."""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

API = "https://api.github.com"
UA = "PixelCard/1.0 (+https://github.com)"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".pixelcard", "cache")


class GitHubError(RuntimeError):
    pass


@dataclass
class RepoCard:
    full_name: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    open_prs: int = 0
    language: str = "-"
    languages: dict = field(default_factory=dict)
    license: str = "none"
    default_branch: str = "main"
    size_kb: int = 0
    topics: list = field(default_factory=list)
    created_at: str = ""
    pushed_at: str = ""
    release_tag: str = ""
    release_date: str = ""
    contributors: int = 0
    weekly_commits: list = field(default_factory=list)  # 52 недели
    archived: bool = False
    homepage: str = ""
    demo: bool = False
    fetched_at: float = 0.0

    # --- производные метрики ---------------------------------------------
    @property
    def issues_only(self) -> int:
        return max(0, self.open_issues - self.open_prs)

    @property
    def days_since_push(self) -> int:
        return days_ago(self.pushed_at)

    @property
    def commits_90d(self) -> int:
        return sum(self.weekly_commits[-13:]) if self.weekly_commits else 0

    @property
    def commits_year(self) -> int:
        return sum(self.weekly_commits)

    def health(self):
        """Простая эвристика «здоровья» репозитория: (score 0..100, grade)."""
        score = 0.0
        d = self.days_since_push
        score += 30 if d <= 7 else 24 if d <= 30 else 15 if d <= 90 else 6 if d <= 365 else 0
        act = self.commits_90d
        score += 25 if act >= 100 else 20 if act >= 40 else 14 if act >= 10 else 7 if act >= 1 else 0
        ratio = self.issues_only / self.stars if self.stars else 1.0
        score += 15 if ratio < 0.02 else 12 if ratio < 0.05 else 8 if ratio < 0.12 else 3
        score += 10 if self.license not in ("none", "", "other") else 3
        score += 10 if self.release_tag else 3
        score += 10 if self.contributors >= 20 else 7 if self.contributors >= 5 else 4 if self.contributors >= 2 else 1
        if self.archived:
            score *= 0.5
        score = max(0, min(100, round(score)))
        grade = ("S" if score >= 92 else "A" if score >= 80 else "B" if score >= 65
                 else "C" if score >= 50 else "D" if score >= 35 else "E")
        return score, grade


def days_ago(iso: str) -> int:
    if not iso:
        return 9999
    try:
        dt = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return 9999
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // 86400))


def human(n) -> str:
    """1234 -> 1.2K, 1250000 -> 1.2M."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "-"
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= limit:
            v = n / limit
            return ("%.1f%s" % (v, suffix)) if v < 10 else ("%d%s" % (round(v), suffix))
    return "%d" % int(n)


class GitHubClient:
    def __init__(self, token=None, cache_dir=CACHE_DIR, ttl=600, timeout=8, offline=False):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.timeout = timeout
        self.offline = offline
        self.rate_remaining = None
        self.rate_limit = None
        os.makedirs(self.cache_dir, exist_ok=True)

    # --- низкий уровень ---------------------------------------------------
    def _cache_path(self, path):
        key = hashlib.sha1(path.encode()).hexdigest()[:20]
        return os.path.join(self.cache_dir, key + ".json")

    def _cache_read(self, path, ttl=None):
        ttl = self.ttl if ttl is None else ttl
        fp = self._cache_path(path)
        try:
            with open(fp) as fh:
                blob = json.load(fh)
        except (OSError, ValueError):
            return None
        if ttl >= 0 and time.time() - blob.get("ts", 0) > ttl:
            return None
        return blob.get("data"), blob.get("headers", {})

    def _cache_write(self, path, data, headers):
        try:
            with open(self._cache_path(path), "w") as fh:
                json.dump({"ts": time.time(), "data": data, "headers": headers}, fh)
        except OSError:
            pass

    def get(self, path, ttl=None, allow_stale=True):
        """GET относительно API. Возвращает (data, headers). Кэш + офлайн-фолбэк."""
        cached = self._cache_read(path, ttl)
        if cached:
            return cached
        if self.offline:
            stale = self._cache_read(path, ttl=-1)
            if stale:
                return stale
            raise GitHubError("offline")
        req = urllib.request.Request(API + path, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8") or "null"
                headers = {k.lower(): v for k, v in resp.headers.items()}
                status = resp.status
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise GitHubError("rate limit / forbidden (%s)" % exc.code)
            if exc.code == 404:
                raise GitHubError("not found")
            raise GitHubError("http %s" % exc.code)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            if allow_stale:
                stale = self._cache_read(path, ttl=-1)
                if stale:
                    return stale
            raise GitHubError("network: %s" % getattr(exc, "reason", exc))
        data = json.loads(raw) if raw.strip() else None
        self._track_rate(headers)
        if status == 202:  # статистика ещё считается на стороне GitHub
            raise GitHubError("stats warming up, retry")
        self._cache_write(path, data, headers)
        return data, headers

    def _headers(self):
        h = {"Accept": "application/vnd.github+json", "User-Agent": UA,
             "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            h["Authorization"] = "Bearer " + self.token
        return h

    def _track_rate(self, headers):
        try:
            self.rate_remaining = int(headers.get("x-ratelimit-remaining"))
            self.rate_limit = int(headers.get("x-ratelimit-limit"))
        except (TypeError, ValueError):
            pass

    @staticmethod
    def _last_page(headers):
        link = headers.get("link", "")
        for part in link.split(","):
            if 'rel="last"' in part:
                url = part.split(">")[0].strip(" <")
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                try:
                    return int(qs.get("page", ["1"])[0])
                except ValueError:
                    return None
        return None

    def _count(self, path):
        try:
            data, headers = self.get(path)
        except GitHubError:
            return 0
        last = self._last_page(headers)
        if last:
            return last
        return len(data) if isinstance(data, list) else 0

    # --- высокий уровень --------------------------------------------------
    def repo_card(self, full_name: str, ttl=None) -> RepoCard:
        """ttl=0 - принудительное обновление, ttl=None - обычный кэш."""
        full_name = full_name.strip().strip("/")
        if full_name.count("/") != 1:
            raise GitHubError("нужен формат owner/repo")
        slow_ttl = 0 if ttl == 0 else 3600
        base = "/repos/" + full_name
        data, _ = self.get(base, ttl=ttl)
        card = RepoCard(
            full_name=data.get("full_name", full_name),
            description=(data.get("description") or "")[:160],
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            watchers=data.get("subscribers_count", 0),
            open_issues=data.get("open_issues_count", 0),
            language=data.get("language") or "-",
            license=((data.get("license") or {}).get("spdx_id") or "none"),
            default_branch=data.get("default_branch", "main"),
            size_kb=data.get("size", 0),
            topics=(data.get("topics") or [])[:6],
            created_at=data.get("created_at") or "",
            pushed_at=data.get("pushed_at") or "",
            archived=bool(data.get("archived")),
            homepage=data.get("homepage") or "",
            fetched_at=time.time(),
        )
        try:
            langs, _ = self.get(base + "/languages", ttl=slow_ttl)
            total = sum(langs.values()) or 1
            card.languages = {k: v * 100.0 / total for k, v in
                              sorted(langs.items(), key=lambda kv: -kv[1])[:5]}
        except (GitHubError, AttributeError):
            pass
        try:
            rel, _ = self.get(base + "/releases/latest", ttl=slow_ttl)
            card.release_tag = (rel or {}).get("tag_name", "") or ""
            card.release_date = ((rel or {}).get("published_at") or "")[:10]
        except GitHubError:
            pass
        try:
            part, _ = self.get(base + "/stats/participation", ttl=slow_ttl)
            card.weekly_commits = list((part or {}).get("all") or [])
        except GitHubError:
            pass
        card.open_prs = self._count(base + "/pulls?state=open&per_page=1")
        card.contributors = self._count(base + "/contributors?per_page=1&anon=1")
        return card

    def search_repos(self, query, limit=8):
        q = urllib.parse.quote(query)
        data, _ = self.get("/search/repositories?q=%s&sort=stars&per_page=%d" % (q, limit), ttl=1800)
        return [(i["full_name"], i.get("stargazers_count", 0)) for i in data.get("items", [])]


# --------------------------------------------------------------- DEMO DATA
DEMO_DESCRIPTIONS = {
    "python/cpython": "The Python programming language",
    "torvalds/linux": "Linux kernel source tree",
    "microsoft/vscode": "Visual Studio Code",
    "rust-lang/rust": "Empowering everyone to build reliable and efficient software",
    "ClickUp/clickup": "One app to replace them all",
}
DEMO_LANGS = [
    {"Python": 78.4, "C": 14.2, "Rust": 4.1, "Shell": 2.0, "Make": 1.3},
    {"TypeScript": 62.0, "JavaScript": 21.5, "CSS": 9.0, "HTML": 5.0, "Shell": 2.5},
    {"Rust": 88.0, "Python": 6.4, "C": 3.1, "Shell": 2.5},
    {"Go": 71.2, "Shell": 12.0, "Dockerfile": 8.3, "Makefile": 8.5},
]


def demo_card(full_name: str) -> RepoCard:
    """Стабильные псевдо-данные (seed от имени) — приложение живое без сети."""
    seed = int(hashlib.sha1(full_name.encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    stars = rnd.choice([rnd.randint(120, 900), rnd.randint(1200, 40000), rnd.randint(50000, 190000)])
    weeks = []
    level = rnd.randint(4, 40)
    for i in range(52):
        level = max(0, int(level + rnd.gauss(0, level * 0.35 + 2)))
        weeks.append(min(level, 400) + (rnd.randint(0, 6) if i > 40 else 0))
    return RepoCard(
        full_name=full_name,
        description=DEMO_DESCRIPTIONS.get(full_name, "demo data - offline mode"),
        stars=stars,
        forks=int(stars * rnd.uniform(0.08, 0.3)),
        watchers=int(stars * rnd.uniform(0.01, 0.05)),
        open_issues=rnd.randint(5, max(6, stars // 60)),
        open_prs=rnd.randint(1, 120),
        language=rnd.choice(["Python", "TypeScript", "Rust", "Go", "C", "Zig"]),
        languages=dict(rnd.choice(DEMO_LANGS)),
        license=rnd.choice(["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "none"]),
        default_branch=rnd.choice(["main", "master", "develop"]),
        size_kb=rnd.randint(500, 900000),
        topics=rnd.sample(["cli", "api", "dev-tools", "pixel-art", "async", "ml", "tui"], 4),
        created_at="2015-%02d-%02dT10:00:00Z" % (rnd.randint(1, 12), rnd.randint(1, 28)),
        pushed_at=datetime.fromtimestamp(
            time.time() - rnd.choice([3600, 86400 * 2, 86400 * 9, 86400 * 60]),
            tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        release_tag="v%d.%d.%d" % (rnd.randint(0, 9), rnd.randint(0, 20), rnd.randint(0, 12)),
        release_date="2026-%02d-%02d" % (rnd.randint(1, 8), rnd.randint(1, 28)),
        contributors=rnd.randint(3, 2400),
        weekly_commits=weeks,
        demo=True,
        fetched_at=time.time(),
    )


DEV_TIPS = [
    "git switch -c fix/bug  -  новая ветка без checkout-магии",
    "python -m venv .venv && . .venv/bin/activate  -  всегда venv",
    "git rebase -i HEAD~5  -  чистая история перед review",
    "pytest -x -q --lf  -  сначала упавшие тесты",
    "python -X dev script.py  -  ловит скрытые warnings",
    "ruff check . --fix  -  быстрый линт вместо десяти тулов",
    "git bisect start  -  бинарный поиск коммита с регрессией",
    "python -m json.tool file.json  -  форматирование без утилит",
    "shell: !!  -  повтор последней команды, а !$ - её аргумент",
    "docker run --rm -it img sh  -  контейнеры без мусора",
    "logging вместо print: level можно выключить, print - нет",
    "dataclasses(slots=True)  -  меньше памяти и опечаток",
    "functools.lru_cache  -  мемоизация в одну строку",
    "python -m timeit -s 'setup' 'code'  -  честный микробенч",
    "git commit --fixup <sha> + rebase --autosquash",
    "readme > wiki: документация рядом с кодом живёт дольше",
    "make review-ready: маленькие PR мержатся в 3 раза быстрее",
    "os.environ.get, а не хардкод секретов в исходниках",
    "grep -rn TODO . | wc -l  -  честный размер технического долга",
    "typing: Protocol вместо ABC для duck typing",
    "asyncio.TaskGroup (3.11+)  -  структурная конкурентность",
    "pathlib.Path вместо os.path.join навсегда",
    "git stash push -m wip  -  подписанные stash не теряются",
    "pip install -e .  -  правки видны без переустановки",
    "subprocess.run(list)  -  без shell=True, без инъекций",
    "contextlib.suppress(FileNotFoundError) вместо пустого except",
    "профилируй перед оптимизацией: cProfile + snakeviz",
    "деплой в пятницу - худший вид смелости",
    "20-минутный помодоро лучше 4 часов в тумане",
    "code review - это про код, а не про людей",
]
