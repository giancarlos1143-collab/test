"""Market-wide and per-ticker sentiment, computed from stored snapshots."""
from . import engine


def _daily_totals(conn, scan_date, need_days):
    """{ticker: avg of daily total options volume over prior days}; {} if too little history."""
    days = [r["d"] for r in conn.execute(
        "SELECT DISTINCT scan_date d FROM scans WHERE scan_date < ? ORDER BY d DESC LIMIT 30",
        (scan_date,))]
    if len(days) < need_days:
        return {}
    q = ",".join("?" * len(days))
    rows = conn.execute(
        f"""SELECT u, AVG(t) a FROM (
              SELECT underlying u, scan_date, SUM(v) t FROM (
                SELECT n.underlying, s.scan_date, n.contract, MAX(n.volume) v FROM snapshots n
                JOIN scans s ON s.id=n.scan_id WHERE s.scan_date IN ({q})
                GROUP BY n.contract, s.scan_date) GROUP BY underlying, scan_date) GROUP BY u""",
        days).fetchall()
    return {r["u"]: r["a"] for r in rows}


def _label(call_share, lo, hi):
    return "Bullish" if call_share >= hi else "Bearish" if call_share <= lo else "Neutral"


def ticker_stats(conn, cfg):
    """Per-ticker totals for the latest scan date (ALL contracts, not just filtered ones)."""
    scan_date = engine.latest_scan_date(conn)
    if not scan_date:
        return {}
    sc = cfg["sentiment"]
    avgs = _daily_totals(conn, scan_date, cfg["scoring"]["history_days"])
    stats = {}
    for r in engine._today_rows(conn, scan_date):
        t = stats.setdefault(r["underlying"], dict(
            ticker=r["underlying"], price=r["underlying_price"], change_pct=r["underlying_change_pct"],
            volume=0, call_volume=0, put_volume=0, call_premium=0.0, put_premium=0.0, contracts=0))
        prem = r["volume"] * (r["price"] or 0) * 100
        t["volume"] += r["volume"]
        t["contracts"] += 1
        if r["kind"] == "call":
            t["call_volume"] += r["volume"]; t["call_premium"] += prem
        else:
            t["put_volume"] += r["volume"]; t["put_premium"] += prem
    for t in stats.values():
        avg = avgs.get(t["ticker"])
        t["avg_volume_30d"] = avg
        t["volume_multiple"] = (t["volume"] / avg) if avg else None
        tot = t["call_premium"] + t["put_premium"]
        t["call_share"] = (t["call_premium"] / tot) if tot else 0.5
        t["bias"] = _label(t["call_share"], sc["ticker_bearish_call_share"], sc["ticker_bullish_call_share"])
        m = t["volume_multiple"]
        t["intensity"] = None if m is None else (
            "High" if m >= sc["intensity_high"] else "Moderate" if m >= sc["intensity_moderate"] else "Low")
    return stats


def market_sentiment(conn, cfg):
    stats = ticker_stats(conn, cfg)
    sc = cfg["sentiment"]
    vals = list(stats.values())
    call_p = sum(t["call_premium"] for t in vals)
    put_p = sum(t["put_premium"] for t in vals)
    share = call_p / (call_p + put_p) if (call_p + put_p) else 0.5
    ranked = sorted(vals, key=lambda t: (t["volume_multiple"] is None, -(t["volume_multiple"] or 0)))
    return dict(
        total_volume=sum(t["volume"] for t in vals),
        total_premium=call_p + put_p, call_premium=call_p, put_premium=put_p,
        call_volume=sum(t["call_volume"] for t in vals), put_volume=sum(t["put_volume"] for t in vals),
        call_share=share, direction=_label(share, sc["bearish_call_share"], sc["bullish_call_share"]),
        building_history=any(t["volume_multiple"] is None for t in vals),
        activity=[dict(ticker=t["ticker"], volume=t["volume"], volume_multiple=t["volume_multiple"])
                  for t in ranked],
        leaders=ranked,
    )
