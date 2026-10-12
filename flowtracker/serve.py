"""One command to run everything:   python3 -m flowtracker.serve

Builds the phone app if needed, starts the scheduler in the background, and serves the app + API on
your network so your iPhone can open it. Prints the address to type into Safari.
"""
import os
import socket
import subprocess
import threading

import uvicorn

from .config import ROOT, load_config

PORT = int(os.getenv("PORT", "8000"))


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))   # no packet is sent; this just picks the right network card
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def build_web():
    web = ROOT / "web"
    if (web / "dist" / "index.html").exists():
        return
    print("Building the app (first run only)...")
    subprocess.run(["npm", "install"], cwd=web, check=True)
    subprocess.run(["npm", "run", "build"], cwd=web, check=True)


def main():
    build_web()
    from . import auth, scheduler
    if os.getenv("RUN_SCHEDULER", "1") == "1":
        threading.Thread(target=scheduler.loop, daemon=True).start()
    ip = lan_ip()
    print(f"\n  On this computer:  http://localhost:{PORT}\n  On your iPhone:    http://{ip}:{PORT}   (same Wi-Fi)")
    print("  Password:          " + ("ON" if auth.password() else "OFF (set APP_PASSWORD in .env before using it away from home)") + "\n")
    uvicorn.run("flowtracker.api:app", host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
