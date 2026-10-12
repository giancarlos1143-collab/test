# Options Flow Tracker

A personal options-flow scanner for your iPhone. It scans unusual options activity, scores each contract
0-100, and shows market sentiment, a watchlist, and a paper-trading results log.

## Quick start (Mac)
    pip3 install -r requirements.txt
    cp .env.example .env            # then open .env and set APP_PASSWORD
    python3 -m flowtracker.simulate # OPTIONAL: fake 45 days of history so you can try everything
    python3 -m flowtracker.fetch    # scan now (uses fake data until you add a Massive key)
    python3 -m flowtracker.serve    # app + scheduled scans; prints the address for your iPhone
Then see `docs/HOSTING.md` for adding it to your iPhone home screen and using it away from home.

## Switching to real data
1. Get a Massive (formerly Polygon.io) API key. Check their pricing page for the cheapest plan that includes
   **option chain snapshots** with volume, open interest and implied volatility.
2. In `.env`: `DATA_PROVIDER=massive` and `MASSIVE_API_KEY=your_key`.
3. If you used the simulator, remove the fake history first: `python3 -m flowtracker.simulate --clear`.
4. `python3 -m flowtracker.fetch NVDA` as a small test, then the full scan.
The Massive code was written from their documentation and could not be tested against the live service, so
expect to check the first real run (field names, rate limits). Volume multiple and IV percentile show
"building history" until 30 days of scans are stored.

## Everyday commands
| Command | What it does |
|---|---|
| `python3 -m flowtracker.serve` | Runs the app and the scheduled scans |
| `python3 -m flowtracker.fetch [TICKERS] [--force]` | Scan now |
| `python3 -m flowtracker.top [N]` | Print today's top scored contracts |
| `python3 -m flowtracker.results [--backfill]` | Update the paper-trading log and print hit rates |
| `python3 -m flowtracker.simulate [--clear]` | Add / remove fake history |
| `python3 -m pytest -q tests` | Run the tests (includes the DRAM worked example) |

## Where things live
- `config.yaml`: scan universe, every scoring threshold, tier names, sentiment cutoffs, schedule.
- `data/flow.db`: SQLite; every scan is kept forever. `.env`: secrets (never committed).
- `flowtracker/`: Python backend (providers, scoring, API). `web/`: the React phone app.
- Every number in the app traces to a stored row: the Detail screen shows its scan and snapshot number.

## Development
    uvicorn flowtracker.api:app --port 8000 --reload     # API (docs at /docs)
    cd web && npm install && npm run dev                 # app at http://localhost:5173
After changing the app, `cd web && npm run build` (serve uses the built copy).

## Not in v1
No bought-at-ask vs sold-at-bid (the `side` field is a placeholder), no Hot News or Profile tabs,
market holidays aren't modelled in the scheduler or the 1/3/5 trading-day results.

## Shareable preview page
    PYTHONPATH=. python3 tools/make_preview.py     # writes preview/index.html (sample-data snapshot, no server needed)
