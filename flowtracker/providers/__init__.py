import os

from .base import ContractSnapshot, OptionsProvider  # noqa: F401


def get_provider(cfg: dict) -> OptionsProvider:
    which = os.getenv("DATA_PROVIDER", "mock").lower()
    if which == "mock":
        from .mock import MockProvider
        return MockProvider()
    if which == "massive":
        from .massive import MassiveProvider
        return MassiveProvider(cfg["provider"]["min_seconds_between_calls"])
    raise RuntimeError(f"Unknown DATA_PROVIDER '{which}'. Use 'mock' or 'massive'.")
