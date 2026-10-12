"""Scores one contract 0-100 from four sub-scores (0-25 each). Pure functions, no database."""
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContractInput:
    volume: int
    open_interest: int
    price: float
    dte: int
    iv_percentile: Optional[float]      # 0-100, None = not enough history
    volume_multiple: Optional[float]    # today's volume / 30d avg, None = not enough history


@dataclass
class Score:
    vol_oi: float
    premium: float
    vol_multiple: float
    expiry_iv: float
    total: float
    tier: Optional[str]
    ratio: float                         # raw V/OI
    dollar_flow: float                   # raw premium
    notes: list[str] = field(default_factory=list)   # e.g. "building history"

    @property
    def parts(self) -> dict:
        return {"vol_oi": self.vol_oi, "premium": self.premium,
                "vol_multiple": self.vol_multiple, "expiry_iv": self.expiry_iv}


def _linear(x: float, zero_at: float, full_at: float, top: float = 25.0) -> float:
    if x <= zero_at:
        return 0.0
    if x >= full_at:
        return top
    return top * (x - zero_at) / (full_at - zero_at)


def _log(x: float, zero_at: float, full_at: float, top: float = 25.0) -> float:
    if x <= zero_at:
        return 0.0
    if x >= full_at:
        return top
    return top * math.log(x / zero_at) / math.log(full_at / zero_at)


def tier_for(total: float, cfg: dict) -> Optional[str]:
    for t in cfg["tiers"]:
        if total >= t["min"]:
            return t["label"]
    return None


def passes_filters(volume: int, price: float, cfg: dict) -> bool:
    return volume >= cfg["min_volume"] and volume * price * 100 >= cfg["min_premium"]


def score_contract(c: ContractInput, cfg: dict) -> Score:
    """cfg is the `scoring:` section of config.yaml."""
    notes = []
    ratio = c.volume / max(c.open_interest, 1)   # brand-new contract (OI 0) counts as max
    s_voi = _linear(ratio, **cfg["vol_oi"])

    flow = c.volume * c.price * 100
    s_prem = _log(flow, **cfg["premium"])

    if c.volume_multiple is None:
        s_mult = float(cfg["neutral_vol_multiple"])
        notes.append("volume multiple: building history")
    else:
        s_mult = _linear(c.volume_multiple, **cfg["vol_multiple"])

    exp_pts = next(e["points"] for e in cfg["expiry_points"] if c.dte <= e["max_dte"])
    ivp = c.iv_percentile
    if ivp is None:
        ivp = cfg["neutral_iv_percentile"]
        notes.append("IV percentile: building history")
    s_exp = min(25.0, exp_pts + min(10.0, ivp / cfg["iv_points_divisor"]))

    total = s_voi + s_prem + s_mult + s_exp
    return Score(s_voi, s_prem, s_mult, s_exp, total, tier_for(total, cfg), ratio, flow, notes)
