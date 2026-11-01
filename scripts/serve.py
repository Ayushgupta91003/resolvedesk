"""Supervise the API and standalone Next server behind one public origin."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
stopping = False

def stop(*_):
    global stopping
    stopping = True

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
children = []
exit_code = 0
try:
    children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "1"], cwd=root / "backend"))
    env = {**os.environ, "HOSTNAME": "0.0.0.0", "PORT": os.getenv("PORT", "10000")}
    children.append(subprocess.Popen(["node", "server.js"], cwd=root / "frontend", env=env))
    while not stopping:
        failed = next((child for child in children if child.poll() is not None), None)
        if failed:
            exit_code = failed.returncode or 1
            print("A service exited; stopping the app so the platform can restart it.", flush=True)
            break
        time.sleep(.5)
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
raise SystemExit(exit_code)
