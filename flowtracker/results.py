"""Results log: record every 80+ play, then check prices 1, 3 and 5 trading days later.

    python3 -m flowtracker.results              # log today's flags + fill in any due outcomes + print summary
    python3 -m flowtracker.results --backfill   # also score every stored past day (useful with history)
A weekday counts as a trading day (market holidays aren't modelled).
"""
import sys
from datetime import date, datetime, timedelta, timezone

from . import db, engine


def add_trading_days(d: date, n: int) -> date:
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def record_flags(conn, cfg, scan_date=None) -> int:
    rc = cfg["results"]
    new = 0
    for r, s in engine.score_all(conn, cfg, scan_date):
        if s.total < rc["min_score"]:
            break  # sorted high to low
        cur = conn.execute(
            """INSERT OR IGNORE INTO flagged_plays (contract, underlying, kind, strike, expiration,
               flag_date, flagged_at, scan_id, snapshot_id, score, tier, stock_price, contract_price)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r["contract"], r["underlying"], r["kind"], r["strike"], r["expiration"],
             scan_date or engine.latest_scan_date(conn), r["scanned_at"], r["scan_id"], r["id"],
             round(s.total, 2), s.tier, r["underlying_price"], r["price"]))
        new += cur.rowcount
    conn.commit()
    return new


def _scan_dates(conn):
    return [r["d"] for r in conn.execute("SELECT DISTINCT scan_date d FROM scans ORDER BY d")]


def _price_on(conn, scan_date, underlying, contract):
    """(stock_price, contract_price, snapshot_id) from the newest snapshots on a scan date."""
    st = conn.execute(
        """SELECT n.underlying_price p FROM snapshots n JOIN scans s ON s.id=n.scan_id
           WHERE s.scan_date=? AND n.underlying=? AND n.underlying_price IS NOT NULL
           ORDER BY n.id DESC LIMIT 1""", (scan_date, underlying)).fetchone()
    ct = conn.execute(
        """SELECT n.id, n.price FROM snapshots n JOIN scans s ON s.id=n.scan_id
           WHERE s.scan_date=? AND n.contract=? ORDER BY n.id DESC LIMIT 1""", (scan_date, contract)).fetchone()
    return (st["p"] if st else None, ct["price"] if ct else None, ct["id"] if ct else None)


def update_outcomes(conn, cfg) -> int:
    rc = cfg["results"]
    dates = _scan_dates(conn)
    added = 0
    for f in conn.execute("SELECT * FROM flagged_plays").fetchall():
        done = {r["horizon"] for r in conn.execute(
            "SELECT horizon FROM flag_outcomes WHERE flag_id=?", (f["id"],))}
        for h in rc["horizons"]:
            if h in done:
                continue
            target = add_trading_days(date.fromisoformat(f["flag_date"]), h)
            limit = target + timedelta(days=rc["max_lookahead_days"])
            actual = next((d for d in dates if target.isoformat() <= d <= limit.isoformat()), None)
            if not actual:
                continue
            sp, cp, sid = _price_on(conn, actual, f["underlying"], f["contract"])
            if sp is None:
                continue
            conn.execute("INSERT INTO flag_outcomes VALUES (?,?,?,?,?,?,?)",
                         (f["id"], h, target.isoformat(), actual, sid, sp, cp))
            added += 1
    conn.commit()
    return added


def backfill(conn, cfg) -> int:
    return sum(record_flags(conn, cfg, d) for d in _scan_dates(conn))


def run(conn, cfg) -> tuple[int, int]:
    return record_flags(conn, cfg), update_outcomes(conn, cfg)


def summary(conn, cfg) -> dict:
    """Hit rate per horizon. A 'hit' = the STOCK moved the way the play bet (call: up, put: down)."""
    out = {}
    for h in cfg["results"]["horizons"]:
        rows = conn.execute(
            """SELECT f.kind, f.stock_price s0, f.contract_price c0, o.stock_price s1, o.contract_price c1
               FROM flag_outcomes o JOIN flagged_plays f ON f.id=o.flag_id WHERE o.horizon=?""", (h,)).fetchall()
        n = hits = 0
        moves, cmoves = [], []
        for r in rows:
            if not r["s0"] or r["s1"] is None:
                continue
            move = (r["s1"] / r["s0"] - 1) * 100 * (1 if r["kind"] == "call" else -1)  # + = in expected direction
            n += 1; hits += move > 0; moves.append(move)
            if r["c0"] and r["c1"] is not None:
                cmoves.append((r["c1"] / r["c0"] - 1) * 100)
        out[h] = dict(horizon=h, measured=n, hits=hits, hit_rate=(hits / n) if n else None,
                      avg_move_pct=(sum(moves) / n) if n else None,
                      avg_contract_change_pct=(sum(cmoves) / len(cmoves)) if cmoves else None)
    total = conn.execute("SELECT COUNT(*) c FROM flagged_plays").fetchone()["c"]
    return dict(total_flagged=total, horizons=list(out.values()))


def flagged_list(conn, cfg, limit=200) -> list[dict]:
    res = []
    for f in conn.execute("SELECT * FROM flagged_plays ORDER BY flag_date DESC, score DESC LIMIT ?", (limit,)):
        d = dict(f)
        d["outcomes"] = {}
        for o in conn.execute("SELECT * FROM flag_outcomes WHERE flag_id=?", (f["id"],)):
            move = ((o["stock_price"] / f["stock_price"] - 1) * 100) if f["stock_price"] and o["stock_price"] else None
            exp = None if move is None else move * (1 if f["kind"] == "call" else -1)
            d["outcomes"][str(o["horizon"])] = dict(
                actual_date=o["actual_date"], stock_price=o["stock_price"], contract_price=o["contract_price"],
                stock_move_pct=move, hit=None if exp is None else exp > 0,
                contract_change_pct=((o["contract_price"] / f["contract_price"] - 1) * 100
                                     if f["contract_price"] and o["contract_price"] is not None else None),
                snapshot_id=o["snapshot_id"])
        res.append(d)
    return res


def main(argv):
    from .config import load_config
    cfg = load_config()
    conn = db.connect(cfg)
    if "--backfill" in argv:
        print(f"Backfill: {backfill(conn, cfg)} flags recorded from stored history")
    new, outs = run(conn, cfg)
    print(f"Logged {new} new flags today, filled {outs} outcomes.\n")
    s = summary(conn, cfg)
    print(f"{s['total_flagged']} plays flagged at {cfg['results']['min_score']}+")
    print(f"{'after':>7}{'measured':>10}{'hit rate':>10}{'avg stock move*':>17}{'avg option chg':>16}")
    for h in s["horizons"]:
        f = lambda v, suf: "n/a" if v is None else f"{v:+.2f}{suf}"
        hr = "n/a" if h["hit_rate"] is None else f"{h['hit_rate']:.0%}"
        print(f"{str(h['horizon'])+'d':>7}{h['measured']:>10}{hr:>10}{f(h['avg_move_pct'], '%'):>17}"
              f"{f(h['avg_contract_change_pct'], '%'):>16}")
    print("* positive = stock moved the way the play bet (calls: up, puts: down)")


if __name__ == "__main__":
    main(sys.argv[1:])
