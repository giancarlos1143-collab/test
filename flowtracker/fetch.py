"""Stage 1 command: fetch chains for the universe, save to SQLite, print a sample.

Run:  python -m flowtracker.fetch            (whole universe)
      python -m flowtracker.fetch NVDA TSLA  (just these)
      add --force to ignore the cache
"""
import sys

from . import db
from .config import load_config, scan_universe
from .providers import get_provider


def main(argv: list[str]) -> None:
    force = "--force" in argv
    tickers = [a.upper() for a in argv if not a.startswith("--")] or None
    run_scan(tickers, force)


def run_scan(tickers=None, force=False) -> None:
    """One full scan: fetch -> save -> results log. Used by the command line and the scheduler."""
    cfg = load_config()
    conn = db.connect(cfg)
    tickers = tickers or scan_universe(cfg, db.watchlist(conn))
    provider = get_provider(cfg)
    scan_id = db.new_scan(conn, provider.name)
    print(f"Scan #{scan_id} using provider '{provider.name}' for {len(tickers)} tickers")

    total = 0
    for t in tickers:
        if not force and provider.name != "mock" and db.recent_ticker_scan(
                conn, t, cfg["provider"]["cache_minutes"]):
            print(f"  {t:5} cached (fetched < {cfg['provider']['cache_minutes']} min ago), skipping")
            continue
        try:
            rows = provider.fetch_chain(t, cfg["provider"]["max_dte"])
        except Exception as e:  # keep going so one bad ticker doesn't kill the scan
            print(f"  {t:5} FAILED: {e}")
            continue
        db.save_snapshots(conn, scan_id, rows)
        total += len(rows)
        print(f"  {t:5} saved {len(rows):5} contracts")
    print(f"Done. {total} contracts stored in {cfg['database']}")
    try:  # log 80+ plays and fill in any due 1/3/5-day outcomes
        from . import results
        new, outs = results.run(conn, cfg)
        print(f"Results log: {new} new flagged plays, {outs} outcomes filled\n")
    except Exception as e:
        print(f"Results log skipped: {e}\n")

    print("Sample: 8 highest-volume contracts in this scan")
    print(f"{'contract':26}{'type':6}{'strike':>8}{'exp':>12}{'price':>8}{'vol':>8}{'OI':>8}{'IV':>7}")
    for r in conn.execute(
            "SELECT * FROM snapshots WHERE scan_id=? ORDER BY volume DESC LIMIT 8", (scan_id,)):
        iv = f"{r['iv']*100:.0f}%" if r["iv"] is not None else "n/a"
        print(f"{r['contract']:26}{r['kind']:6}{r['strike']:>8.1f}{r['expiration']:>12}"
              f"{(r['price'] or 0):>8.2f}{r['volume']:>8}{r['open_interest']:>8}{iv:>7}")


if __name__ == "__main__":
    main(sys.argv[1:])
