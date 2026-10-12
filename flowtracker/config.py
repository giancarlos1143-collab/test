"""Loads config.yaml and .env."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def load_config() -> dict:
    with open(ROOT / "config.yaml") as f:
        cfg = yaml.safe_load(f)
    if os.getenv("FLOW_DB"):          # lets tests use a throwaway database
        cfg["database"] = os.environ["FLOW_DB"]
    return cfg


def scan_universe(cfg: dict, extra: list[str] | None = None) -> list[str]:
    """config universe + config watchlist + watchlist stored in the database (`extra`)."""
    seen: list[str] = []
    for t in list(cfg.get("universe") or []) + list(cfg.get("watchlist") or []) + list(extra or []):
        t = t.upper().strip()
        if t and t not in seen:
            seen.append(t)
    return seen
