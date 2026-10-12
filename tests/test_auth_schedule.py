import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from flowtracker import api, db
from flowtracker.config import load_config
from flowtracker.scheduler import due_scan

NY = ZoneInfo("America/New_York")


def test_password_gate(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "hunter2")
    c = TestClient(api.app)
    assert c.get("/api/health").status_code == 200                      # open
    assert c.get("/api/top-plays").status_code == 401                   # locked
    assert c.get("/api/session").json() == {"password_required": True, "logged_in": False}
    assert c.post("/api/login", json={"password": "nope"}).status_code == 401
    assert c.get("/api/top-plays").status_code == 401
    assert c.post("/api/login", json={"password": "hunter2"}).status_code == 200
    assert c.get("/api/top-plays").status_code == 200                   # cookie now set
    assert TestClient(api.app).get("/api/top-plays").status_code == 401  # a different browser is still locked
    c.cookies.set("flow_session", "999999999999.forged")
    assert c.get("/api/top-plays").status_code == 401


def test_no_password_means_open(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "")
    assert TestClient(api.app).get("/api/top-plays").status_code == 200


def _mem(scan_times):
    conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA)
    for t in scan_times:
        conn.execute("INSERT INTO scans (scanned_at, scan_date, provider) VALUES (?,?,?)",
                     (t.astimezone(ZoneInfo("UTC")).isoformat(), t.date().isoformat(), "mock"))
    return conn


def test_schedule_after_close_runs_once():
    cfg = load_config()
    mon = lambda h, m: datetime(2026, 10, 12, h, m, tzinfo=NY)           # a Monday
    assert due_scan(_mem([]), cfg, mon(15, 0)) is None                    # market hours, intraday off
    assert due_scan(_mem([]), cfg, mon(16, 29)) is None                   # before 16:30
    assert due_scan(_mem([]), cfg, mon(16, 31)) == "after_close"
    assert due_scan(_mem([mon(16, 32)]), cfg, mon(17, 0)) is None         # already done today
    assert due_scan(_mem([mon(10, 0)]), cfg, mon(17, 0)) == "after_close"  # a morning scan doesn't count
    assert due_scan(_mem([]), cfg, datetime(2026, 10, 10, 17, 0, tzinfo=NY)) is None  # Saturday


def test_intraday_when_enabled():
    cfg = load_config(); cfg["schedule"]["intraday_minutes"] = 30
    mon = lambda h, m: datetime(2026, 10, 12, h, m, tzinfo=NY)
    assert due_scan(_mem([]), cfg, mon(10, 0)) == "intraday"
    assert due_scan(_mem([mon(10, 0)]), cfg, mon(10, 20)) is None
    assert due_scan(_mem([mon(10, 0)]), cfg, mon(10, 31)) == "intraday"
    assert due_scan(_mem([]), cfg, mon(9, 0)) is None                     # before the open
