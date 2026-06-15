"""Start the app in dev or production mode.

Dev (default):  python start.py
  - FastAPI with --reload on :8000
  - Vite dev server with hot-reload on :5173

Prod:           python start.py --prod
  - Builds the frontend, then serves everything from FastAPI on :8000
"""
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"


def stream(proc: subprocess.Popen, prefix: str) -> None:
    for line in proc.stdout:
        print(f"{prefix} {line}", end="")


def run_prod() -> None:
    print("Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        shell=True,
    )
    if result.returncode != 0:
        print("Frontend build failed.")
        sys.exit(1)

    print("Starting server on http://localhost:8000\n")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT,
    )
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        proc.terminate()


def run_dev() -> None:
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
    )

    threading.Thread(target=stream, args=(backend, "[api]    "), daemon=True).start()
    threading.Thread(target=stream, args=(frontend, "[vite]   "), daemon=True).start()

    print("Started. API on :8000, UI on :5173. Press Ctrl+C to stop both.\n")
    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        backend.terminate()
        frontend.terminate()


def main() -> None:
    if "--prod" in sys.argv:
        run_prod()
    else:
        run_dev()


if __name__ == "__main__":
    main()
