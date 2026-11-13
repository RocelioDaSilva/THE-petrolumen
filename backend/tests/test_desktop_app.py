import json
import importlib.util
import re
import socket
import sys
import types
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest


def test_desktop_launcher_starts_embedded_api(monkeypatch, tmp_path):
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

    def start(**kwargs):
        state["webview_start_kwargs"] = kwargs
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

        auth_url = f"http://127.0.0.1:{state['port']}/api/auth/register"
        registration = urllib.request.Request(
            auth_url,
            data=json.dumps(
                {
                    "username": "desktop-user",
                    "email": "desktop-user@example.test",
                    "password": "desktop-password",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(registration, timeout=15) as response:
            assert response.status == 201

        token_request = urllib.request.Request(
            f"http://127.0.0.1:{state['port']}/api/auth/token",
            data=json.dumps(
                {"username": "desktop-user", "password": "desktop-password"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(token_request, timeout=15) as response:
            access_token = json.loads(response.read())["access_token"]

        current_user = urllib.request.Request(
            f"http://127.0.0.1:{state['port']}/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(current_user, timeout=15) as response:
            assert json.loads(response.read())["username"] == "desktop-user"

        state["shutdown"]()

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

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("PETROLUMEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("PETROLUMEN_DATABASE_URL", raising=False)
    desktop_app.main()

    assert state["shutdown"].__name__ == "shutdown"
    assert state["webview_start_kwargs"] == {
        "icon": str(desktop_app._resource_path("public/petrolumen.ico")),
        "private_mode": False,
        "storage_path": str(tmp_path / "PetroLumen" / "webview"),
    }
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", state["port"]), timeout=0.25)
    data_dir = tmp_path / "PetroLumen"
    secret = (data_dir / "secret.key").read_text(encoding="utf-8")
    assert len(secret) >= 32
    assert sys.modules["app.main"].app.state.database_manager.db_url == (
        f"sqlite:///{(data_dir / 'petrolumen.db').resolve().as_posix()}"
    )
