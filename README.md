# Options Flow Tracker

Personal options-flow scanner. Built in stages (see the build spec).

## Stage 1: data pipeline
    pip install -r requirements.txt
    cp .env.example .env          # then edit .env
    python3 -m flowtracker.fetch  # fetch + save + print sample

`DATA_PROVIDER=mock` uses fake data (no key). `DATA_PROVIDER=massive` uses the real API
and needs `MASSIVE_API_KEY` in `.env`. Edit `config.yaml` to change tickers/rate limits.

## Stage 2: scoring
    python3 -m pytest -q tests     # includes the DRAM worked example
    python3 -m flowtracker.top     # today's top 10 scored contracts (add a number for more)
All thresholds are in the `scoring:` section of `config.yaml`.

### Mock history simulator
    python3 -m flowtracker.simulate          # backfill 32 fake trading days
    python3 -m flowtracker.fetch             # then add today's scan
    python3 -m flowtracker.simulate --clear  # remove the fake history (before using real data)

## Stage 3: backend API
    uvicorn flowtracker.api:app --port 8000     # interactive docs at http://127.0.0.1:8000/docs
Endpoints: `/api/top-plays`, `/api/contracts/{id}`, `/api/sentiment`, `/api/tickers/{T}`,
`/api/watchlist` (GET/POST, DELETE `/api/watchlist/{T}`). Watchlist tickers are saved in the
database and included in the next `fetch`.
