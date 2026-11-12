from __future__ import annotations

import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

import uvicorn
import webview
from fastapi.staticfiles import StaticFiles


def _resource_path(relative_path: str) -> Path:
    bundle_root = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    )
    return bundle_root / relative_path


class DesktopApi:
    def __init__(self, port: int) -> None:
        self._port = port

    def get_port(self) -> int:
        return self._port


def main() -> None:
    repository_root = Path(__file__).resolve().parent.parent
    backend_path = repository_root / "backend"
    sys.path.insert(0, str(backend_path))

    if "PETROLUMEN_SECRET_KEY" not in os.environ:
        os.environ["PETROLUMEN_SECRET_KEY"] = secrets.token_urlsafe(48)

    from app.main import app

    web_root = _resource_path("dist")
    index_path = web_root / "index.html"
    if not index_path.is_file():
        raise FileNotFoundError(
            f"Built React app not found at {index_path}. Run `npm run build` first."
        )
    app.mount("/ui", StaticFiles(directory=web_root, html=True), name="desktop-ui")

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
        f"http://127.0.0.1:{port}/ui/?{urlencode({'api_port': port})}",
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
