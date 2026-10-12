import sqlite3
from datetime import date

from flowtracker import db, results
from flowtracker.config import load_config

CFG = load_config()


def test_trading_days_skip_weekends():
    fri = date(2026, 10, 9)
    assert results.add_trading_days(fri, 1) == date(2026, 10, 12)   # Fri -> Mon
    assert results.add_trading_days(fri, 5) == date(2026, 10, 16)
    assert results.add_trading_days(date(2026, 10, 12), 3) == date(2026, 10, 15)


def test_hit_logic_calls_up_puts_down():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA)
    flags = [  # (kind, stock at flag, stock 1d later)
        ("call", 100, 102),   # hit  (+2%)
        ("call", 100, 99),    # miss (-1%)
        ("put", 100, 97),     # hit  (stock fell)
        ("put", 100, 101),    # miss (stock rose)
    ]
    for i, (kind, s0, s1) in enumerate(flags, 1):
        conn.execute("INSERT INTO flagged_plays (id, contract, underlying, kind, flag_date, flagged_at, score, stock_price, contract_price)"
                     " VALUES (?,?,?,?,?,?,?,?,?)", (i, f"C{i}", "X", kind, "2026-10-09", "t", 85, s0, 1.0))
        conn.execute("INSERT INTO flag_outcomes VALUES (?,?,?,?,?,?,?)", (i, 1, "2026-10-12", "2026-10-12", None, s1, 1.5))
    s = results.summary(conn, CFG)
    h1 = s["horizons"][0]
    assert (h1["measured"], h1["hits"], h1["hit_rate"]) == (4, 2, 0.5)
    assert abs(h1["avg_move_pct"] - 0.75) < 1e-9          # (+2 -1 +3 -1) / 4 = 0.75
    assert abs(h1["avg_contract_change_pct"] - 50) < 1e-9
    lst = results.flagged_list(conn, CFG)
    assert {x["contract"]: x["outcomes"]["1"]["hit"] for x in lst} == {"C1": True, "C2": False, "C3": True, "C4": False}
