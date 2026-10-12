"""Plain-English sentences for each sub-score."""


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def explain(r: dict, s) -> dict:
    ratio = s.ratio
    voi = (f"Volume is {ratio:.1f}x open interest, so mostly new positions."
           if ratio >= 2 else f"Volume is {ratio:.1f}x open interest, so mostly existing positions trading.")
    prem = f"${s.dollar_flow:,.0f} changed hands ({r['volume']:,} contracts at ${r['price']:.2f})."
    if r["volume_multiple"] is None:
        mult = "Not enough history yet (building history), so a neutral score is used."
    else:
        mult = (f"Volume is {r['volume_multiple']:.1f}x this contract's 30-day average "
                f"of {r['avg_volume']:,.0f}.")
    ivp = r["iv_percentile"]
    exp = (f"{r['dte']} days to expiry; shorter expiries score higher. " +
           (f"IV is at the {ordinal(round(ivp))} percentile." if ivp is not None
            else "IV percentile still building history (neutral 50 used)."))
    return {"vol_oi": voi, "premium": prem, "vol_multiple": mult, "expiry_iv": exp}
