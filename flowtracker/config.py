"""Loads config.yaml and .env."""
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def load_config() -> dict:
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def scan_universe(cfg: dict) -> list[str]:
    seen: list[str] = []
    for t in list(cfg.get("universe") or []) + list(cfg.get("watchlist") or []):
        t = t.upper().strip()
        if t and t not in seen:
            seen.append(t)
    return seen
