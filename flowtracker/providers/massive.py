"""Massive (formerly Polygon.io) options provider: option chain snapshot endpoint."""
import os
import time
from datetime import date, datetime

import requests

from .base import ContractSnapshot

BASE_URL = "https://api.massive.com"


class MassiveProvider:
    name = "massive"

    def __init__(self, min_seconds_between_calls: float = 13):
        self.key = os.getenv("MASSIVE_API_KEY", "").strip()
        if not self.key:
            raise RuntimeError("MASSIVE_API_KEY is missing. Add it to your .env file.")
        self.gap = min_seconds_between_calls
        self._last_call = 0.0

    def _get(self, url: str, params: dict | None = None) -> dict:
        wait = self.gap - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(4):
            self._last_call = time.time()
            r = requests.get(
                url, params=params, headers={"Authorization": f"Bearer {self.key}"}, timeout=30
            )
            if r.status_code == 429:  # rate limited: back off and retry
                time.sleep(15 * (attempt + 1))
                continue
            if r.status_code in (401, 403):
                raise RuntimeError(
                    f"Massive rejected the request ({r.status_code}): "
                    f"{r.json().get('message', r.text)[:200]}"
                )
            r.raise_for_status()
            return r.json()
        raise RuntimeError("Massive rate limit: gave up after retries")

    def fetch_chain(self, ticker: str, max_dte: int) -> list[ContractSnapshot]:
        today = date.today()
        out: list[ContractSnapshot] = []
        url = f"{BASE_URL}/v3/snapshot/options/{ticker}"
        params = {
            "limit": 250,
            "expiration_date.lte": date.fromordinal(today.toordinal() + max_dte).isoformat(),
        }
        while url:
            data = self._get(url, params)
            for item in data.get("results", []):
                d = item.get("details", {})
                day = item.get("day", {}) or {}
                und = item.get("underlying_asset", {}) or {}
                out.append(
                    ContractSnapshot(
                        underlying=ticker,
                        contract=d.get("ticker", ""),
                        kind=d.get("contract_type", ""),
                        strike=float(d.get("strike_price", 0)),
                        expiration=d.get("expiration_date", ""),
                        price=day.get("close") or (item.get("last_trade") or {}).get("price"),
                        volume=int(day.get("volume") or 0),
                        open_interest=int(item.get("open_interest") or 0),
                        iv=item.get("implied_volatility"),
                        underlying_price=und.get("price"),
                    )
                )
            url = data.get("next_url")
            params = None  # next_url already carries its cursor
        return out
