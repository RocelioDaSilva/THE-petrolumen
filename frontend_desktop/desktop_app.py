from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview
from fastapi.middleware.cors import CORSMiddleware


def _resource_path(relative_path: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / relative_path


class DesktopApi:
    def __init__(self, port: int) -> None:
        self._port = port

    def get_port(self) -> int:
        return self._port


def main() -> None:
    repository_root = Path(__file__).resolve().parent.parent
    backend_path = repository_root / "backend"
    sys.path.insert(0, str(repository_root))
    sys.path.insert(0, str(backend_path))

    from backend.app.main import app

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(2048)
    port = listener.getsockname()[1]

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(
        target=server.run,
        kwargs={"sockets": [listener]},
        name="petrolumen-api",
        daemon=True,
    )
    server_thread.start()

    deadline = time.monotonic() + 5
    ready = False
    while time.monotonic() < deadline:
        if not server_thread.is_alive():
            raise RuntimeError("The embedded FastAPI server stopped during startup.")
        if server.started:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    ready = True
                    break
            except OSError:
                pass
        time.sleep(0.05)
    if not ready:
        server.should_exit = True
        server_thread.join(timeout=2)
        raise RuntimeError("The embedded FastAPI server did not start within 5 seconds.")

    api = DesktopApi(port)
    window = webview.create_window(
        "PetroLumen",
        _resource_path("static/index.html").as_uri(),
        js_api=api,
        width=1280,
        height=850,
        min_size=(900, 600),
    )

    def shutdown() -> None:
        server.should_exit = True
        server_thread.join(timeout=5)

    window.events.closed += shutdown
    try:
        webview.start()
    finally:
        shutdown()


if __name__ == "__main__":
    main()
