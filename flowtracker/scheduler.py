"""Runs scans on a schedule: once after the close, plus optional intraday scans.

Started automatically by `python3 -m flowtracker.serve`. Or alone: `python3 -m flowtracker.scheduler`.
Weekends are skipped (market holidays aren't modelled; a holiday scan just repeats the last prices).
"""
import time
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import db
from .config import load_config


def _hm(text: str):
    h, m = text.split(":")
    return int(h), int(m)


def due_scan(conn, cfg, now: datetime):
    """Returns 'after_close', 'intraday' or None for the given local time. Pure decision logic."""
    sc = cfg["schedule"]
    if now.weekday() >= 5:
        return None
    tz = ZoneInfo(sc["timezone"])
    today = now.date().isoformat()
    since = (now - timedelta(days=2)).astimezone(ZoneInfo("UTC")).isoformat()
    rows = [datetime.fromisoformat(r["scanned_at"]).astimezone(tz)
            for r in conn.execute("SELECT scanned_at FROM scans WHERE scanned_at >= ?", (since,))]
    rows = [t for t in rows if t.date().isoformat() == today]
    minutes = now.hour * 60 + now.minute
    close_h, close_m = _hm(sc["after_close_time"])
    if minutes >= close_h * 60 + close_m:
        done = any(t.hour * 60 + t.minute >= close_h * 60 + close_m for t in rows)
        return None if done else "after_close"
    every = sc.get("intraday_minutes") or 0
    o_h, o_m = _hm(sc["market_open"]); c_h, c_m = _hm(sc["market_close"])
    if every and o_h * 60 + o_m <= minutes <= c_h * 60 + c_m:
        last = max(rows, default=None)
        if last is None or (now - last).total_seconds() >= every * 60:
            return "intraday"
    return None


def loop(poll_seconds: int = 60):
    from .fetch import run_scan
    print("Scheduler running (after-close scan + optional intraday).", flush=True)
    while True:
        try:
            cfg = load_config()
            now = datetime.now(ZoneInfo(cfg["schedule"]["timezone"]))
            kind = due_scan(db.connect(cfg), cfg, now)
            if kind:
                print(f"[{now:%Y-%m-%d %H:%M}] starting {kind} scan", flush=True)
                run_scan()
        except Exception:
            traceback.print_exc()
        time.sleep(poll_seconds)


if __name__ == "__main__":
    loop()
