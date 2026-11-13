import json
import importlib.util
import os
import re
import socket
import sys
import types
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest


def _load_desktop_app():
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
    return desktop_app


def test_desktop_launcher_starts_embedded_api(monkeypatch, tmp_path):
    state = {}

    class ClosedEvent:
        def __iadd__(self, callback):
            state["shutdown"] = callback
            self.callback = callback
            return self

        def fire(self):
            assert self.callback is not None
            self.callback()

    class Window:
        def __init__(self):
            closed_event = ClosedEvent()
            self.events = types.SimpleNamespace(closed=closed_event)
            state["close_window"] = closed_event.fire

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

        state["close_window"]()

    webview_stub = types.ModuleType("webview")
    webview_stub.create_window = create_window
    webview_stub.start = start
    monkeypatch.setitem(sys.modules, "webview", webview_stub)
    monkeypatch.setenv("PETROLUMEN_SECRET_KEY", "desktop-test-secret-key-at-least-32")

    desktop_app = _load_desktop_app()

    server_join_calls = [0]
    server_join_timeouts = []
    original_join = desktop_app.threading.Thread.join

    def count_server_join(thread, *args, **kwargs):
        if thread.name == "petrolumen-api":
            server_join_calls[0] += 1
            server_join_timeouts.append(kwargs.get("timeout"))
        return original_join(thread, *args, **kwargs)

    monkeypatch.setattr(desktop_app.threading.Thread, "join", count_server_join)
    monkeypatch.setattr(
        desktop_app.os,
        "_exit",
        lambda code: pytest.fail(f"Unexpected forced process exit: {code}"),
    )
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.delenv("PETROLUMEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("PETROLUMEN_DATABASE_URL", raising=False)
    desktop_app.main()

    assert server_join_calls == [1]
    assert server_join_timeouts == [2]
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
    assert (data_dir / "webview").is_dir()
    assert (data_dir / "petrolumen.db").is_file()
    assert sys.modules["app.main"].app.state.database_manager.db_url == (
        f"sqlite:///{(data_dir / 'petrolumen.db').resolve().as_posix()}"
    )


def test_user_data_falls_back_to_roaming_app_data_on_permission_error(
    monkeypatch, tmp_path
):
    webview_stub = types.ModuleType("webview")
    monkeypatch.setitem(sys.modules, "webview", webview_stub)
    desktop_app = _load_desktop_app()

    local_app_data = tmp_path / "Local"
    local_data_dir = local_app_data / "PetroLumen"
    roaming_data_dir = tmp_path / "Roaming" / "PetroLumen"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("APPDATA", str(roaming_data_dir.parent))
    monkeypatch.delenv("PETROLUMEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("PETROLUMEN_DATABASE_URL", raising=False)

    path_type = type(local_data_dir)
    original_mkdir = path_type.mkdir

    def deny_local_directory(path, *args, **kwargs):
        if path == local_data_dir:
            raise PermissionError("test permission failure")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(path_type, "mkdir", deny_local_directory)

    result = desktop_app._configure_user_data()

    assert result == roaming_data_dir
    assert not local_data_dir.exists()
    assert (roaming_data_dir / "secret.key").is_file()
    assert (roaming_data_dir / "webview").is_dir()
    assert os.environ["PETROLUMEN_DATABASE_URL"] == (
        f"sqlite:///{(roaming_data_dir / 'petrolumen.db').resolve().as_posix()}"
    )


def test_user_data_falls_back_to_executable_data_when_appdata_is_unwritable(
    monkeypatch, tmp_path
):
    webview_stub = types.ModuleType("webview")
    monkeypatch.setitem(sys.modules, "webview", webview_stub)
    desktop_app = _load_desktop_app()

    local_data_dir = tmp_path / "Local" / "PetroLumen"
    roaming_data_dir = tmp_path / "Roaming" / "PetroLumen"
    executable_dir = tmp_path / "install"
    bundle_dir = tmp_path / "bundle"
    executable_dir.mkdir()
    bundle_dir.mkdir()
    expected_data_dir = executable_dir / "data"

    monkeypatch.setattr(desktop_app.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        desktop_app.sys, "executable", str(executable_dir / "PetroLumen.exe")
    )
    monkeypatch.setattr(desktop_app.sys, "_MEIPASS", str(bundle_dir), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(local_data_dir.parent))
    monkeypatch.setenv("APPDATA", str(roaming_data_dir.parent))
    monkeypatch.delenv("PETROLUMEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("PETROLUMEN_DATABASE_URL", raising=False)

    original_ensure_writable_directory = desktop_app._ensure_writable_directory

    def deny_appdata(directory):
        if directory in (local_data_dir, roaming_data_dir):
            raise PermissionError("test AppData restriction")
        original_ensure_writable_directory(directory)

    monkeypatch.setattr(
        desktop_app, "_ensure_writable_directory", deny_appdata
    )

    result = desktop_app._configure_user_data()

    assert result == expected_data_dir
    assert (expected_data_dir / "secret.key").is_file()
    assert (expected_data_dir / "webview").is_dir()
    assert os.environ["PETROLUMEN_DATABASE_URL"] == (
        f"sqlite:///{(expected_data_dir / 'petrolumen.db').resolve().as_posix()}"
    )


def test_shutdown_forces_exit_when_api_thread_does_not_stop(monkeypatch):
    desktop_app = _load_desktop_app()

    class Server:
        should_exit = False

    class StuckThread:
        joined_with = None

        def join(self, timeout=None):
            self.joined_with = timeout

        def is_alive(self):
            return True

    server = Server()
    server_thread = StuckThread()

    def force_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(desktop_app.os, "_exit", force_exit)

    with pytest.raises(SystemExit) as exit_error:
        desktop_app._shutdown_server(server, server_thread)

    assert exit_error.value.code == 0
    assert server.should_exit is True
    assert server_thread.joined_with == 2


def test_user_data_falls_back_when_local_directory_is_not_writable(
    monkeypatch, tmp_path
):
    webview_stub = types.ModuleType("webview")
    monkeypatch.setitem(sys.modules, "webview", webview_stub)
    desktop_app = _load_desktop_app()

    local_app_data = tmp_path / "Local"
    local_data_dir = local_app_data / "PetroLumen"
    roaming_data_dir = tmp_path / "Roaming" / "PetroLumen"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("APPDATA", str(roaming_data_dir.parent))
    monkeypatch.delenv("PETROLUMEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("PETROLUMEN_DATABASE_URL", raising=False)

    original_temporary_file = desktop_app.tempfile.TemporaryFile

    def deny_local_write(*args, **kwargs):
        if Path(kwargs["dir"]) == local_data_dir:
            raise PermissionError("test directory is not writable")
        return original_temporary_file(*args, **kwargs)

    monkeypatch.setattr(desktop_app.tempfile, "TemporaryFile", deny_local_write)

    result = desktop_app._configure_user_data()

    assert result == roaming_data_dir
    assert local_data_dir.is_dir()
    assert (roaming_data_dir / "secret.key").is_file()
    assert (roaming_data_dir / "webview").is_dir()
    assert os.environ["PETROLUMEN_DATABASE_URL"] == (
        f"sqlite:///{(roaming_data_dir / 'petrolumen.db').resolve().as_posix()}"
    )
