"""Tests run against a throwaway database filled with mock data, never your real one or your .env."""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["FLOW_DB"] = os.path.join(_tmp, "test.db")
os.environ["DATA_PROVIDER"] = "mock"   # .env can't override variables that are already set
os.environ["APP_PASSWORD"] = ""

from flowtracker import fetch, simulate  # noqa: E402

simulate.main([])
fetch.run_scan()
