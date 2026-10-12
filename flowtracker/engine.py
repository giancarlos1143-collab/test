"""Scores the latest stored snapshots, using stored history for averages and IV percentile."""
from bisect import bisect_right
from datetime import date

from . import db
from .scoring import ContractInput, Score, passes_filters, score_contract


def latest_scan_date(conn):
    r = conn.execute("SELECT MAX(scan_date) d FROM scans").fetchone()
    return r["d"]


def _today_rows(conn, scan_date):
    """Newest snapshot of each contract on scan_date."""
    return conn.execute(
        """SELECT n.* , s.scanned_at FROM snapshots n JOIN scans s ON s.id = n.scan_id
           WHERE s.scan_date = ? AND n.id IN (
             SELECT MAX(n2.id) FROM snapshots n2 JOIN scans s2 ON s2.id = n2.scan_id
             WHERE s2.scan_date = ? GROUP BY n2.contract)""", (scan_date, scan_date)).fetchall()


def _avg_volumes(conn, scan_date, need_days):
    """{contract: 30-day average volume} from the prior days, only where enough days exist."""
    days = [r["d"] for r in conn.execute(
        "SELECT DISTINCT scan_date d FROM scans WHERE scan_date < ? ORDER BY d DESC LIMIT 30",
        (scan_date,))]
    if len(days) < need_days:
        return {}
    q = ",".join("?" * len(days))
    rows = conn.execute(
        f"""SELECT contract, AVG(v) a, COUNT(*) c FROM (
              SELECT n.contract, s.scan_date, MAX(n.volume) v FROM snapshots n
              JOIN scans s ON s.id=n.scan_id WHERE s.scan_date IN ({q})
              GROUP BY n.contract, s.scan_date) GROUP BY contract""", days).fetchall()
    # a contract with fewer than need_days days of its own data has no reliable average yet
    return {r["contract"]: r["a"] for r in rows if r["c"] >= need_days}


def _iv_history(conn, scan_date, need_days):
    """{underlying: sorted list of past IVs} over up to 252 prior days; {} if too little history."""
    days = [r["d"] for r in conn.execute(
        "SELECT DISTINCT scan_date d FROM scans WHERE scan_date < ? ORDER BY d DESC LIMIT 252",
        (scan_date,))]
    if len(days) < need_days:
        return {}
    q = ",".join("?" * len(days))
    out = {}
    for r in conn.execute(
            f"""SELECT n.underlying u, n.iv FROM snapshots n JOIN scans s ON s.id=n.scan_id
                WHERE s.scan_date IN ({q}) AND n.iv IS NOT NULL""", days):
        out.setdefault(r["u"], []).append(r["iv"])
    return {u: sorted(v) for u, v in out.items()}


_cache = {"key": None, "val": None}


def score_all(conn, cfg, scan_date=None) -> list[tuple[dict, Score]]:
    """Scores newest-per-contract snapshots of a scan date (default: latest). Cached until a new scan."""
    key = (conn.execute("SELECT MAX(id) m FROM scans").fetchone()["m"], scan_date)
    if _cache.get("key") == (key, id(cfg)):
        return _cache["val"]
    sc = cfg["scoring"]
    scan_date = scan_date or latest_scan_date(conn)
    if not scan_date:
        return []
    today = date.fromisoformat(scan_date)
    avgs = _avg_volumes(conn, scan_date, sc["history_days"])
    ivs = _iv_history(conn, scan_date, sc["history_days"])
    out = []
    for r in _today_rows(conn, scan_date):
        price = r["price"] or 0
        if not passes_filters(r["volume"], price, sc):
            continue
        avg = avgs.get(r["contract"]) or r["avg_volume_30d"]
        mult = (r["volume"] / avg) if avg else None
        hist = ivs.get(r["underlying"])
        ivp = (100.0 * bisect_right(hist, r["iv"]) / len(hist)) if hist and r["iv"] is not None else None
        dte = (date.fromisoformat(r["expiration"]) - today).days
        s = score_contract(ContractInput(r["volume"], r["open_interest"], price, dte, ivp, mult), sc)
        out.append(({**dict(r), "dte": dte, "iv_percentile": ivp, "volume_multiple": mult,
                     "avg_volume": avg}, s))
    out.sort(key=lambda x: x[1].total, reverse=True)
    _cache.update(key=(key, id(cfg)), val=out)
    return out
