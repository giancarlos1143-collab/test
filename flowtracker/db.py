"""SQLite storage. Every scan is kept forever (one row per contract per scan)."""
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT
from .providers.base import ContractSnapshot

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL,         -- UTC ISO timestamp
    scan_date TEXT NOT NULL,          -- YYYY-MM-DD (UTC)
    provider TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    underlying TEXT NOT NULL,
    contract TEXT NOT NULL,
    kind TEXT NOT NULL,
    strike REAL, expiration TEXT,
    price REAL, volume INTEGER, open_interest INTEGER, iv REAL,
    underlying_price REAL, underlying_change_pct REAL,
    avg_volume_30d REAL,
    side TEXT                          -- placeholder, empty in v1
);
CREATE INDEX IF NOT EXISTS ix_snap_scan ON snapshots(scan_id);
CREATE INDEX IF NOT EXISTS ix_snap_contract ON snapshots(contract, scan_id);
"""


def connect(cfg: dict) -> sqlite3.Connection:
    path = Path(cfg["database"])
    path = path if path.is_absolute() else ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def new_scan(conn, provider: str) -> int:
    now = datetime.now(timezone.utc)
    cur = conn.execute(
        "INSERT INTO scans (scanned_at, scan_date, provider) VALUES (?,?,?)",
        (now.isoformat(timespec="seconds"), now.date().isoformat(), provider),
    )
    conn.commit()
    return cur.lastrowid


def save_snapshots(conn, scan_id: int, rows: list[ContractSnapshot]) -> None:
    cols = ["underlying", "contract", "kind", "strike", "expiration", "price", "volume",
            "open_interest", "iv", "underlying_price", "underlying_change_pct",
            "avg_volume_30d", "side"]
    conn.executemany(
        f"INSERT INTO snapshots (scan_id, {','.join(cols)}) VALUES (?,{','.join('?'*len(cols))})",
        [(scan_id, *[asdict(r)[c] for c in cols]) for r in rows],
    )
    conn.commit()


def recent_ticker_scan(conn, ticker: str, max_age_minutes: int):
    """Return scan_id if this ticker was already fetched recently (cache), else None."""
    row = conn.execute(
        """SELECT s.id, s.scanned_at FROM scans s JOIN snapshots n ON n.scan_id = s.id
           WHERE n.underlying = ? ORDER BY s.id DESC LIMIT 1""", (ticker,)).fetchone()
    if not row:
        return None
    age = datetime.now(timezone.utc) - datetime.fromisoformat(row["scanned_at"])
    return row["id"] if age.total_seconds() < max_age_minutes * 60 else None
