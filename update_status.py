"""Build docs/status.json from the official results pages. Run by GitHub Actions."""
import json, os
from datetime import datetime, timezone
from draw_checker import is_draw_reached, draw_datetime, fetch_latest_results, compare

TZ, DATE, TIME = "Europe/London", "2026-10-23", "20:15"
MAIN, STARS = [9, 11, 17, 33, 45], [8, 10]

dt = draw_datetime(TZ, DATE, TIME)
now = datetime.now(timezone.utc)
latest = fetch_latest_results()
official = None
if latest:
    main, stars, source = latest
    c = compare(MAIN, STARS, main, stars)
    official = {"main": main, "stars": stars, "source": source,
                "matched_main": c["matched_main"], "matched_stars": c["matched_stars"],
                "prize_category": c["prize_category"]}
status = {
    "generated_at": now.isoformat(timespec="seconds"),
    "draw_time": dt.isoformat(),
    "draw_reached": is_draw_reached(TZ, DATE, TIME),
    "seconds_to_draw": max(0, int((dt.astimezone(timezone.utc) - now).total_seconds())),
    "target": {"main": MAIN, "stars": STARS},
    "latest_published": official,
}
os.makedirs("docs", exist_ok=True)
with open("docs/status.json", "w") as f:
    json.dump(status, f, indent=2)
print(json.dumps({k: status[k] for k in ("generated_at", "draw_reached", "seconds_to_draw")}))
