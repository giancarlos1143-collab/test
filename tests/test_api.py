from fastapi.testclient import TestClient

from flowtracker import api, engine

client = TestClient(api.app)


def test_top_plays_sorted_and_60_plus():
    d = client.get("/api/top-plays").json()
    scores = [p["score"] for p in d["plays"]]
    assert d["count"] == len(scores) > 0 and scores == sorted(scores, reverse=True)
    assert min(scores) >= 60 and d["last_updated"]


def test_contract_detail_breakdown_sums_to_score():
    top = client.get("/api/top-plays").json()["plays"][0]
    d = client.get(f"/api/contracts/{top['contract']}").json()
    assert abs(sum(v["score"] for v in d["breakdown"].values()) - d["score"]) < 0.06
    assert all(v["explanation"] for v in d["breakdown"].values())
    assert client.get("/api/contracts/NOPE").status_code == 404


def test_sentiment_and_ticker():
    s = client.get("/api/sentiment").json()
    assert s["direction"] in ("Bullish", "Neutral", "Bearish") and len(s["leaders"]) >= 16
    t = client.get("/api/tickers/spy").json()
    assert t["ticker"] == "SPY" and "30-day average" in t["summary"]
    assert client.get("/api/tickers/ZZZZ").status_code == 404


def test_watchlist_roundtrip():
    assert client.post("/api/watchlist", json={"ticker": "dram"}).status_code == 201
    assert "DRAM" in [w["ticker"] for w in client.get("/api/watchlist").json()["watchlist"]]
    client.delete("/api/watchlist/DRAM")
    assert "DRAM" not in [w["ticker"] for w in client.get("/api/watchlist").json()["watchlist"]]
    assert client.post("/api/watchlist", json={"ticker": "bad ticker!"}).status_code == 422
