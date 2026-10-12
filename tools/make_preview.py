"""Builds a single self-contained HTML preview of the app from the current database (no server needed).

    python3 tools/make_preview.py     ->  writes preview/index.html
"""
import json
import os
import pathlib
import subprocess
from urllib.parse import quote

os.environ["APP_PASSWORD"] = ""
os.environ.setdefault("DATA_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402

from flowtracker import api  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
c = TestClient(api.app)


def get(path):
    r = c.get(path)
    r.raise_for_status()
    return r.json()


top = get("/api/top-plays?limit=100")
sentiment = get("/api/sentiment")
results = get("/api/results?limit=100")
tickers = {t["ticker"]: get(f"/api/tickers/{t['ticker']}") for t in sentiment["leaders"]}
ids = {p["contract"] for p in top["plays"]}
ids |= {p["contract"] for t in tickers.values() for p in t["top_contracts"]}
contracts = {i: get(f"/api/contracts/{quote(i, safe='')}") for i in sorted(ids)}
data = dict(topPlays=top, sentiment=sentiment, results=results, tickers=tickers, contracts=contracts,
            initialWatchlist=["PLTR", "NVDA", "GME"])
(ROOT / "web/src/demo-data.json").write_text(json.dumps(data, separators=(",", ":")))
print(f"snapshot: {len(top['plays'])} plays, {len(contracts)} contract pages, {len(tickers)} tickers")

env = dict(os.environ, VITE_DEMO="1")
subprocess.run(["npm", "run", "build"], cwd=ROOT / "web", env=env, check=True, capture_output=True)
dist = ROOT / "web/dist-preview/assets"
js = next(dist.glob("*.js")).read_text().replace("</script", "<\\/script")
css = next(dist.glob("*.css")).read_text()
html = f"""<title>Options Flow Tracker</title>
<style>
:root {{ color-scheme: dark; }}
{css}
</style>
<div id="root"></div>
<script type="module">
{js}
</script>
"""
out = ROOT / "preview"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html)
print(f"wrote {out/'index.html'} ({len(html)/1024:.0f} KB)")
