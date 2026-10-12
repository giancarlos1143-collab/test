"""Scores the latest stored snapshots, using stored history for averages and IV percentile."""
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


def _avg_volume(conn, contract, scan_date, need_days):
    """30-day average volume for a contract from prior days. None until enough days exist."""
    rows = conn.execute(
        """SELECT s.scan_date, MAX(n.volume) v FROM snapshots n JOIN scans s ON s.id=n.scan_id
           WHERE n.contract=? AND s.scan_date < ? GROUP BY s.scan_date
           ORDER BY s.scan_date DESC LIMIT 30""", (contract, scan_date)).fetchall()
    return (sum(r["v"] for r in rows) / len(rows)) if len(rows) >= need_days else None


def _iv_percentile(conn, underlying, iv, scan_date, need_days):
    """Where today's IV sits among this underlying's past IVs (0-100). None until enough days."""
    rows = conn.execute(
        """SELECT n.iv FROM snapshots n JOIN scans s ON s.id=n.scan_id
           WHERE n.underlying=? AND s.scan_date < ? AND n.iv IS NOT NULL
           AND s.scan_date IN (SELECT DISTINCT s3.scan_date FROM scans s3 WHERE s3.scan_date < ?
                               ORDER BY s3.scan_date DESC LIMIT 252)""",
        (underlying, scan_date, scan_date)).fetchall()
    days = conn.execute("SELECT COUNT(DISTINCT scan_date) c FROM scans WHERE scan_date < ?",
                        (scan_date,)).fetchone()["c"]
    if days < need_days or not rows or iv is None:
        return None
    return 100.0 * sum(1 for r in rows if r["iv"] <= iv) / len(rows)


def score_all(conn, cfg) -> list[tuple[dict, Score]]:
    sc = cfg["scoring"]
    scan_date = latest_scan_date(conn)
    if not scan_date:
        return []
    today = date.fromisoformat(scan_date)
    out = []
    for r in _today_rows(conn, scan_date):
        price = r["price"] or 0
        if not passes_filters(r["volume"], price, sc):
            continue
        avg = _avg_volume(conn, r["contract"], scan_date, sc["history_days"]) or r["avg_volume_30d"]
        mult = (r["volume"] / avg) if avg else None
        ivp = _iv_percentile(conn, r["underlying"], r["iv"], scan_date, sc["history_days"])
        dte = (date.fromisoformat(r["expiration"]) - today).days
        s = score_contract(ContractInput(r["volume"], r["open_interest"], price, dte, ivp, mult), sc)
        out.append(({**dict(r), "dte": dte, "iv_percentile": ivp, "volume_multiple": mult}, s))
    out.sort(key=lambda x: x[1].total, reverse=True)
    return out
