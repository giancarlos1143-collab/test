"""Backend API.   uvicorn flowtracker.api:app --reload --port 8000     (docs at /docs)"""
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from . import analytics, db, engine, results
from .config import load_config, scan_universe
from .explain import explain

app = FastAPI(title="Options Flow Tracker")
CFG = load_config()


def conn():
    return db.connect(CFG)


def _last_updated(c):
    r = c.execute("SELECT MAX(scanned_at) m FROM scans").fetchone()
    return r["m"]


def _play(r, s):
    return dict(
        contract=r["contract"], ticker=r["underlying"], kind=r["kind"], strike=r["strike"],
        price=r["price"], dte=r["dte"], expiration=r["expiration"], volume=r["volume"],
        open_interest=r["open_interest"], premium=round(s.dollar_flow, 2), vol_oi=round(s.ratio, 2), iv=r["iv"],
        score=round(s.total, 1), tier=s.tier, scored_at=r["scanned_at"])


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/top-plays")
def top_plays(min_score: float = 60, limit: int = 100):
    c = conn()
    plays = [_play(r, s) for r, s in engine.score_all(c, CFG) if s.total >= min_score][:limit]
    return {"last_updated": _last_updated(c), "count": len(plays), "plays": plays}


@app.get("/api/contracts/{contract}")
def contract_detail(contract: str):
    c = conn()
    for r, s in engine.score_all(c, CFG):
        if r["contract"] == contract:
            text = explain(r, s)
            sub = {k: dict(score=round(v, 2), max=25, explanation=text[k]) for k, v in s.parts.items()}
            hist = c.execute(
                """SELECT sc.scan_date d, MAX(n.volume) v FROM snapshots n JOIN scans sc ON sc.id=n.scan_id
                   WHERE n.contract=? GROUP BY sc.scan_date ORDER BY d DESC LIMIT 30""", (contract,)).fetchall()
            return dict(
                **_play(r, s), iv_percentile=r["iv_percentile"], volume_multiple=r["volume_multiple"],
                avg_volume=r["avg_volume"], underlying_price=r["underlying_price"], side=r["side"],
                notes=s.notes, breakdown=sub, snapshot_id=r["id"], scan_id=r["scan_id"],
                volume_history=[dict(date=h["d"], volume=h["v"]) for h in hist],
                last_updated=_last_updated(c))
    raise HTTPException(404, "Contract not scored today (it may be filtered out or not in the latest scan)")


@app.get("/api/sentiment")
def sentiment():
    c = conn()
    return {"last_updated": _last_updated(c), **analytics.market_sentiment(c, CFG)}


@app.get("/api/tickers/{ticker}")
def ticker_page(ticker: str):
    c = conn()
    t = analytics.ticker_stats(c, CFG).get(ticker.upper())
    if not t:
        raise HTTPException(404, f"No data for {ticker.upper()} in the latest scan")
    m, avg = t["volume_multiple"], t["avg_volume_30d"]
    summary = (f"Today's options volume is {m:.1f}x the 30-day average of {avg:,.0f}." if m
               else "Not enough history yet to compare with a 30-day average.")
    cs = t["call_share"] * 100
    read = f"{cs:.0f}% of volume is in calls and {100-cs:.0f}% in puts: {t['bias'].lower()} lean."
    top = [_play(r, s) for r, s in engine.score_all(c, CFG) if r["underlying"] == t["ticker"]][:5]
    return {"last_updated": _last_updated(c), **t, "summary": summary, "read": read, "top_contracts": top}


@app.get("/api/results")
def results_log(limit: int = 100):
    c = conn()
    return {"last_updated": _last_updated(c), "min_score": CFG["results"]["min_score"],
            **results.summary(c, CFG), "plays": results.flagged_list(c, CFG, limit)}


class TickerIn(BaseModel):
    ticker: str


@app.get("/api/watchlist")
def get_watchlist():
    c = conn()
    stats = analytics.ticker_stats(c, CFG)
    scored = engine.score_all(c, CFG)
    rows = []
    for tk in db.watchlist(c):
        t = stats.get(tk, {})
        top = next((_play(r, s) for r, s in scored if r["underlying"] == tk), None)
        rows.append(dict(ticker=tk, price=t.get("price"), change_pct=t.get("change_pct"),
                         volume_multiple=t.get("volume_multiple"), top_contract=top,
                         in_latest_scan=tk in stats))
    return {"last_updated": _last_updated(c), "watchlist": rows}


def _fetch_one(ticker: str):
    """Pull a fresh chain for one ticker (runs in the background after it's added to the watchlist)."""
    from .providers import get_provider
    try:
        c = conn()
        prov = get_provider(CFG)
        rows = prov.fetch_chain(ticker, CFG["provider"]["max_dte"])
        db.save_snapshots(c, db.new_scan(c, prov.name), rows)
    except Exception as e:  # never crash the server over a data hiccup
        print(f"background fetch for {ticker} failed: {e}")


@app.post("/api/watchlist", status_code=201)
def add_watch(body: TickerIn, bg: BackgroundTasks):
    tk = body.ticker.upper().strip()
    if not tk.isalnum() or len(tk) > 6:
        raise HTTPException(422, "Ticker must be 1-6 letters/digits")
    c = conn()
    c.execute("INSERT OR IGNORE INTO watchlist VALUES (?,?)",
              (tk, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    c.commit()
    if tk not in analytics.ticker_stats(c, CFG):
        bg.add_task(_fetch_one, tk)
    return {"ticker": tk, "scan_universe_size": len(scan_universe(CFG, db.watchlist(c)))}


@app.delete("/api/watchlist/{ticker}")
def remove_watch(ticker: str):
    c = conn()
    c.execute("DELETE FROM watchlist WHERE ticker=?", (ticker.upper(),))
    c.commit()
    return {"removed": ticker.upper()}
