"""Prints today's top scored contracts.   python -m flowtracker.top [N]"""
import sys

from . import db
from .config import load_config
from .engine import score_all


def main(argv):
    n = int(argv[0]) if argv else 10
    cfg = load_config()
    conn = db.connect(cfg)
    scored = score_all(conn, cfg)
    if not scored:
        print("Nothing scored. Run `python3 -m flowtracker.fetch` first.")
        return
    shown = scored[:n]
    print(f"{len(scored)} contracts passed the filters; "
          f"{sum(1 for _, s in scored if s.tier)} score 60+. Top {len(shown)}:\n")
    print(f"{'#':>2} {'score':>5} {'tier':15}{'contract':24}{'type':5}{'strike':>7}{'DTE':>4}"
          f"{'premium':>10}{'V/OI':>6}  sub-scores (voi/prem/mult/exp)")
    for i, (r, s) in enumerate(shown, 1):
        p = s.parts
        print(f"{i:>2} {s.total:>5.1f} {(s.tier or '-'):15}{r['contract']:24}{r['kind']:5}"
              f"{r['strike']:>7.1f}{r['dte']:>4}{'$%.0fK' % (s.dollar_flow/1000):>10}"
              f"{s.ratio:>5.1f}x  {p['vol_oi']:.0f}/{p['premium']:.0f}/{p['vol_multiple']:.0f}/{p['expiry_iv']:.1f}")
    if any(s.notes for _, s in shown):
        print("\nNote: 'building history' - fewer than 30 days stored, so volume multiple uses a "
              "neutral 12 and IV percentile a neutral 50.")


if __name__ == "__main__":
    main(sys.argv[1:])
