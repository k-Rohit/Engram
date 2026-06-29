"""Launch Cognee's built-in web UI (and its backend) over your ingested data.

Usage:  PYTHONPATH=. uv run python scripts/run_cognee_ui.py
Then open http://localhost:3000

start_ui() spawns a subprocess; we keep this parent alive so the UI keeps
running. Ctrl-C to stop.
"""

import time

from backend.config import configure_cognee


def main() -> None:
    configure_cognee()
    import cognee

    proc = cognee.start_ui(
        pid_callback=lambda pid: print(f"[cognee-ui] subprocess pid={pid}"),
        port=3000,
        open_browser=True,
        auto_download=True,    # download prebuilt UI assets on first run
        start_backend=True,    # serve the data the UI reads from
        backend_port=8000,     # the Cognee frontend expects its backend on :8000
    )
    print("Cognee UI -> http://localhost:3000  (backend on :8000)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        if proc:
            proc.terminate()


if __name__ == "__main__":
    main()
