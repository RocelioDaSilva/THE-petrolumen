import json
import importlib.util
import re
import sys
import types
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit


def test_desktop_launcher_starts_embedded_api(monkeypatch):
    state = {}

    class ClosedEvent:
        def __iadd__(self, callback):
            state["shutdown"] = callback
            return self

    class Window:
        def __init__(self):
            self.events = types.SimpleNamespace(closed=ClosedEvent())

    def create_window(title, uri, **kwargs):
        assert title == "PetroLumen"
        parsed_uri = urlsplit(uri)
        assert parsed_uri.path == "/ui/"
        state["port"] = kwargs["js_api"].get_port()
        assert parsed_uri.port == state["port"]
        assert parsed_uri.query == f"api_port={state['port']}"
        state["uri"] = uri
        return Window()

    def start():
        with urllib.request.urlopen(state["uri"], timeout=3) as response:
            assert response.status == 200
            html = response.read().decode("utf-8")
            assert '<div id="root"></div>' in html
        script_match = re.search(r'<script[^>]+src="([^"]+\.js)"', html)
        assert script_match is not None
        with urllib.request.urlopen(urljoin(state["uri"], script_match.group(1)), timeout=3) as response:
            assert response.status == 200
            assert len(response.read()) > 0

        health_url = f"http://127.0.0.1:{state['port']}/health"
        desktop_origin = f"http://127.0.0.1:{state['port']}"
        request = urllib.request.Request(health_url, headers={"Origin": desktop_origin})
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 200
            assert json.loads(response.read())["status"] == "ok"
            assert response.headers["Access-Control-Allow-Origin"] == desktop_origin

        external_origin = urllib.request.Request(
            health_url,
            headers={"Origin": "https://example.com"},
        )
        with urllib.request.urlopen(external_origin, timeout=3) as response:
            assert "Access-Control-Allow-Origin" not in response.headers

        preflight = urllib.request.Request(
            health_url,
            method="OPTIONS",
            headers={
                "Origin": desktop_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        with urllib.request.urlopen(preflight, timeout=3) as response:
            assert response.status == 200
            assert response.headers["Access-Control-Allow-Origin"] == desktop_origin

    webview_stub = types.ModuleType("webview")
    webview_stub.create_window = create_window
    webview_stub.start = start
    monkeypatch.setitem(sys.modules, "webview", webview_stub)
    monkeypatch.setenv("PETROLUMEN_SECRET_KEY", "desktop-test-secret-key-at-least-32")

    desktop_path = (
        Path(__file__).resolve().parents[2]
        / "frontend_desktop"
        / "desktop_app.py"
    )
    spec = importlib.util.spec_from_file_location(
        "petrolumen_desktop_app_test", desktop_path
    )
    assert spec is not None and spec.loader is not None
    desktop_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(desktop_app)

    desktop_app.main()

    assert state["shutdown"].__name__ == "shutdown"
