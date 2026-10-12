import pytest

from flowtracker.config import load_config
from flowtracker.scoring import ContractInput, passes_filters, score_contract

CFG = load_config()["scoring"]

# DRAM $61 call: 2 DTE, IV pct 55, volume 6000, OI 1400, vol multiple 4.4x, price $0.41
DRAM = ContractInput(volume=6000, open_interest=1400, price=0.41, dte=2,
                     iv_percentile=55, volume_multiple=4.4)


def test_dram_example_prints_every_subscore(capsys):
    s = score_contract(DRAM, CFG)
    with capsys.disabled():
        print("\n--- DRAM $61 call worked example ---")
        print(f"V/OI          {s.ratio:.2f}x          -> {s.vol_oi:5.2f} / 25")
        print(f"Premium       ${s.dollar_flow:,.0f}     -> {s.premium:5.2f} / 25")
        print(f"Vol multiple  4.4x            -> {s.vol_multiple:5.2f} / 25")
        print(f"Expiry + IV   2 DTE, IV 55%   -> {s.expiry_iv:5.2f} / 25")
        print(f"TOTAL                         -> {s.total:5.2f} / 100  [{s.tier}]")
    assert s.vol_oi == 25                       # 4.3x is above the 4.0x cap
    assert s.premium == pytest.approx(13.3, abs=0.1)   # $246K on the log curve
    assert s.vol_multiple == pytest.approx(21.25)       # "about 21"
    assert s.expiry_iv == pytest.approx(20.5)           # 15 + 5.5
    assert s.total == pytest.approx(80.05, abs=0.1)
    assert s.tier == "STRONG STICKUP"


def test_boundaries():
    lo = score_contract(ContractInput(1000, 1000, 0.5, 40, 0, 1.0), CFG)
    assert lo.vol_oi == 0 and lo.vol_multiple == 0
    hi = score_contract(ContractInput(100000, 1000, 5.0, 0, 100, 9.0), CFG)
    assert hi.vol_oi == 25 and hi.premium == 25 and hi.vol_multiple == 25
    assert hi.expiry_iv == 25 and hi.total == 100 and hi.tier == "ROBBERY"


def test_building_history_uses_neutral_scores():
    s = score_contract(ContractInput(6000, 1400, 0.41, 2, None, None), CFG)
    assert s.vol_multiple == 12
    assert s.expiry_iv == pytest.approx(20.0)   # 15 + neutral IV 50 -> 5
    assert len(s.notes) == 2


def test_expiry_buckets():
    pts = lambda d: score_contract(ContractInput(1, 1, 1, d, 0, 1), CFG).expiry_iv
    assert (pts(0), pts(2), pts(3), pts(7), pts(8), pts(30), pts(31)) == (15, 15, 12, 12, 7, 7, 3)


def test_zero_open_interest_does_not_crash():
    assert score_contract(ContractInput(1000, 0, 1.0, 1, 50, 2), CFG).vol_oi == 25


def test_filters():
    assert passes_filters(500, 10.0, CFG)          # $500K
    assert not passes_filters(499, 10.0, CFG)      # volume too low
    assert not passes_filters(600, 0.5, CFG)       # $30K premium too low
