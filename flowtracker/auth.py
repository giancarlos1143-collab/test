"""Optional password protection. Set APP_PASSWORD in .env to turn it on; leave it empty for no password.

The browser logs in once and keeps a signed cookie for 90 days. The data API refuses requests without it.
"""
import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request, Response

COOKIE = "flow_session"
MAX_AGE = 90 * 24 * 3600
_fails: dict[str, list[float]] = {}


def password() -> str:
    return os.getenv("APP_PASSWORD", "").strip()


def _sign(expiry: str) -> str:
    key = hashlib.sha256(("flowtracker|" + password()).encode()).digest()
    return hmac.new(key, expiry.encode(), hashlib.sha256).hexdigest()


def make_token() -> str:
    expiry = str(int(time.time()) + MAX_AGE)
    return f"{expiry}.{_sign(expiry)}"


def valid_token(token: str | None) -> bool:
    if not password():
        return True
    try:
        expiry, sig = (token or "").split(".")
        return int(expiry) > time.time() and hmac.compare_digest(sig, _sign(expiry))
    except ValueError:
        return False


def login(request: Request, response: Response, given: str) -> None:
    ip = request.client.host if request.client else "?"
    recent = [t for t in _fails.get(ip, []) if time.time() - t < 600]
    if len(recent) >= 8:
        raise HTTPException(429, "Too many wrong passwords. Try again in 10 minutes.")
    if not password() or hmac.compare_digest(given.encode(), password().encode()):
        response.set_cookie(COOKIE, make_token(), max_age=MAX_AGE, httponly=True, samesite="lax",
                            secure=request.headers.get("x-forwarded-proto") == "https")
        return
    _fails[ip] = recent + [time.time()]
    time.sleep(0.5)
    raise HTTPException(401, "Wrong password")
