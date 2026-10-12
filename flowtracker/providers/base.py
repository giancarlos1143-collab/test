"""The contract every data source must follow.

To switch to ThetaData later, write a new class with the same `fetch_chain`
method and register it in providers/__init__.py. Nothing else changes.
"""
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class ContractSnapshot:
    underlying: str
    contract: str            # e.g. O:NVDA251219C00150000
    kind: str                # "call" or "put"
    strike: float
    expiration: str          # YYYY-MM-DD
    price: Optional[float]   # last/close price of the option
    volume: int
    open_interest: int
    iv: Optional[float]      # implied volatility, e.g. 0.55 = 55%
    underlying_price: Optional[float]
    underlying_change_pct: Optional[float] = None
    avg_volume_30d: Optional[float] = None  # provider's average, if it has one
    side: Optional[str] = None  # placeholder: "ask"/"bid" once the data source can tell


class OptionsProvider(Protocol):
    name: str

    def fetch_chain(self, ticker: str, max_dte: int) -> list[ContractSnapshot]: ...
