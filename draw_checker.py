"""Draw verification: fetch official EuroMillions results and compare."""
from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DRAW_DATETIME_LOCAL = None  # set via init


def draw_datetime(tz_name: str = "Europe/London", date: str = "2026-10-23", time: str = "20:15") -> datetime:
    tz = ZoneInfo(tz_name)
    d = datetime.strptime(date, "%Y-%m-%d").date()
    h, m = time.split(":")
    return datetime(d.year, d.month, d.day, int(h), int(m), tzinfo=tz)


def is_draw_reached(tz_name="Europe/London", date="2026-10-23", time="20:15") -> bool:
    return datetime.now(ZoneInfo(tz_name)) >= draw_datetime(tz_name, date, time)


def prize_category(matched_main: int, matched_stars: int) -> str:
    if matched_main == 5 and matched_stars == 2:
        return "Jackpot (5+2)"
    if matched_main == 5 and matched_stars == 1:
        return "5+1"
    if matched_main == 5 and matched_stars == 0:
        return "5+0"
    if matched_main == 4 and matched_stars == 2:
        return "4+2"
    if matched_main == 4 and matched_stars == 1:
        return "4+1"
    if matched_main == 4 and matched_stars == 0:
        return "4+0"
    if matched_main == 3 and matched_stars == 2:
        return "3+2"
    if matched_main == 3 and matched_stars == 1:
        return "3+1"
    if matched_main == 3 and matched_stars == 0:
        return "3+0"
    if matched_main == 2 and matched_stars == 2:
        return "2+2"
    if matched_main == 2 and matched_stars == 1:
        return "2+1"
    if matched_main == 1 and matched_stars == 2:
        return "1+2"
    if matched_main == 0 and matched_stars == 2:
        return "0+2"
    return "No prize"


SOURCES = [
    ("euromillions.com", "https://www.euro-millions.com/results"),
    ("lotto.net", "https://www.lotto.net/euromillions/results"),
]


def _fetch(url: str, timeout: int = 20) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; EuroMillionsFocusEngine/1.0)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def _parse_all_draws(html: str) -> list[tuple[list[int], list[int]]]:
    if not html:
        return []
    results = []
    for block in re.findall(r'<ul class="balls">(.*?)</ul>', html, re.S):
        main = [int(x) for x in re.findall(r'class="resultBall ball">\s*(\d{1,2})\s*<', block)]
        stars = [int(x) for x in re.findall(r'class="resultBall lucky-star">\s*(\d{1,2})\s*<', block)]
        if len(main) == 5 and len(stars) == 2 and len(set(main)) == 5 and len(set(stars)) == 2:
            if all(1 <= n <= 50 for n in main) and all(1 <= n <= 12 for n in stars):
                results.append((sorted(main), sorted(stars)))
    return results


def _parse_numbers(html: str) -> tuple[list[int], list[int]] | None:
    draws = _parse_all_draws(html)
    return draws[0] if draws else None


def fetch_recent_draws(limit: int = 20) -> list[tuple[list[int], list[int]]]:
    draws = []
    for name, url in SOURCES:
        html = _fetch(url)
        parsed = _parse_all_draws(html) if html else []
        if parsed:
            draws = parsed[:limit]
            break
    return draws


def historical_frequency(limit: int = 20) -> dict | None:
    draws = fetch_recent_draws(limit)
    if len(draws) < 5:
        return None
    from collections import Counter
    main_c = Counter()
    star_c = Counter()
    for m, s in draws:
        main_c.update(m)
        star_c.update(s)
    n = len(draws)
    return {
        "draws": n,
        "main_frequency": {num: (main_c.get(num, 0), main_c.get(num, 0) / n) for num in range(1, 51)},
        "star_frequency": {num: (star_c.get(num, 0), star_c.get(num, 0) / n) for num in range(1, 13)},
        "note": "Observational only. Does not affect future draw probabilities.",
    }



def fetch_latest_results() -> tuple[list[int], list[int], str] | None:
    """Return (main, stars, source_name) or None."""
    for name, url in SOURCES:
        html = _fetch(url)
        parsed = _parse_numbers(html) if html else None
        if parsed:
            main, stars = parsed
            return main, stars, name
    return None


def wait_for_results(max_wait_minutes: int = 120, poll_seconds: int = 60) -> tuple[list[int], list[int], str] | None:
    import time
    deadline = datetime.now(timezone.utc) + timedelta(minutes=max_wait_minutes)
    while datetime.now(timezone.utc) < deadline:
        res = fetch_latest_results()
        if res:
            return res
        time.sleep(poll_seconds)
    return None


def compare(target_main, target_stars, official_main, official_stars) -> dict:
    tm = set(target_main); ts = set(target_stars)
    om = set(official_main); os_ = set(official_stars)
    mm = len(tm & om)
    ms = len(ts & os_)
    return {
        "target_main": sorted(target_main),
        "target_stars": sorted(target_stars),
        "official_main": sorted(official_main),
        "official_stars": sorted(official_stars),
        "matched_main": mm,
        "matched_stars": ms,
        "prize_category": prize_category(mm, ms),
    }
