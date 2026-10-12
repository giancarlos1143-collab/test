# Options Flow Tracker

Personal options-flow scanner. Built in stages (see the build spec).

## Stage 1: data pipeline
    pip install -r requirements.txt
    cp .env.example .env          # then edit .env
    python3 -m flowtracker.fetch  # fetch + save + print sample

`DATA_PROVIDER=mock` uses fake data (no key). `DATA_PROVIDER=massive` uses the real API
and needs `MASSIVE_API_KEY` in `.env`. Edit `config.yaml` to change tickers/rate limits.
