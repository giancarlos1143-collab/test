"""Backfill fake history so the 30-day features can be tried with mock data.

    python3 -m flowtracker.simulate           # add ~32 past trading days of fake scans
    python3 -m flowtracker.simulate --clear   # remove them again
Run `python3 -m flowtracker.fetch` afterwards so today's scan is the newest one.
"""
import sys
from datetime import date, datetime, timedelta, timezone

from . import db
from .config import load_config, scan_universe
from .providers.mock import MockProvider

SIM_TAG = "mock-sim"
DAYS = 32


def main(argv):
    cfg = load_config()
    conn = db.connect(cfg)
    if "--clear" in argv:
        ids = [r["id"] for r in conn.execute("SELECT id FROM scans WHERE provider=?", (SIM_TAG,))]
        for i in ids:
            conn.execute("DELETE FROM snapshots WHERE scan_id=?", (i,))
            conn.execute("DELETE FROM scans WHERE id=?", (i,))
        conn.commit()
        print(f"Removed {len(ids)} simulated scans.")
        return
    if conn.execute("SELECT 1 FROM scans WHERE provider=?", (SIM_TAG,)).fetchone():
        print("Simulated history already exists. Use --clear first to rebuild it.")
        return
    tickers = scan_universe(cfg)
    max_dte = cfg["provider"]["max_dte"]
    day, made = date.today() - timedelta(days=1), 0
    while made < DAYS:
        if day.weekday() < 5:  # Mon-Fri only
            at = datetime(day.year, day.month, day.day, 21, 0, tzinfo=timezone.utc)
            cur = conn.execute("INSERT INTO scans (scanned_at, scan_date, provider) VALUES (?,?,?)",
                               (at.isoformat(timespec="seconds"), day.isoformat(), SIM_TAG))
            prov = MockProvider(as_of=day)
            for t in tickers:
                db.save_snapshots(conn, cur.lastrowid, prov.fetch_chain(t, max_dte))
            made += 1
        day -= timedelta(days=1)
    print(f"Added {made} simulated trading days of history ({tickers[0]}...{tickers[-1]}).")


if __name__ == "__main__":
    main(sys.argv[1:])
