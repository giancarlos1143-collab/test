"""Fake but realistic data so the app runs with no API key. Numbers are random-but-seeded."""
import random
from datetime import date, timedelta

from .base import ContractSnapshot

BASE_PRICES = {"SPY": 560, "QQQ": 480, "IWM": 220, "PLTR": 75, "NVDA": 135, "TSLA": 250,
               "AAPL": 230, "AMD": 160, "META": 580, "GME": 28, "IREN": 12, "WULF": 6,
               "IBIT": 55, "CRWV": 90, "ORCL": 170, "XLF": 48}


class MockProvider:
    name = "mock"

    def __init__(self, as_of: date | None = None):
        # as_of only changes the random volumes/IV (used by the history simulator).
        # Expiry dates always come from the real today, so a contract keeps the same ID across days.
        self.as_of = as_of or date.today()

    def fetch_chain(self, ticker: str, max_dte: int) -> list[ContractSnapshot]:
        rnd = random.Random(f"{ticker}-{self.as_of}")
        spot = BASE_PRICES.get(ticker, 100)
        change = round(rnd.uniform(-3, 3), 2)
        out = []
        for dte in (0, 2, 5, 9, 16, 30):
            if dte > max_dte:
                continue
            exp = (date.today() + timedelta(days=dte)).isoformat()
            for kind in ("call", "put"):
                for step in range(-4, 5):
                    strike = round(spot * (1 + step * 0.02), 0)
                    dist = abs(step)
                    oi = int(rnd.uniform(300, 8000) / (1 + dist * 0.3) * rnd.choice([0.1, 0.3, 1, 1, 2]))
                    vol = int(oi * rnd.choices([0.05, 0.15, 0.3, 0.6, 1.5, 4.5], weights=[30, 30, 20, 12, 6, 2])[0] * rnd.uniform(0.5, 1.5))
                    price = round(max(0.05, spot * 0.02 / (1 + dist) * (1 + dte / 30)), 2)
                    out.append(ContractSnapshot(
                        underlying=ticker,
                        contract=f"O:{ticker}{exp.replace('-', '')[2:]}{kind[0].upper()}{int(strike*1000):08d}",
                        kind=kind, strike=strike, expiration=exp, price=price,
                        volume=vol, open_interest=oi, iv=round(rnd.uniform(0.25, 0.9), 3),
                        underlying_price=spot, underlying_change_pct=change,
                    ))
        return out
