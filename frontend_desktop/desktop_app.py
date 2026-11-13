from __future__ import annotations

import logging
import os
import secrets
import socket
import sys
import tempfile
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import ModuleType
from urllib.parse import urlencode

import uvicorn
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

WEBVIEW2_DOWNLOAD_URL = "https://developer.microsoft.com/microsoft-edge/webview2/"
DOTNET_FRAMEWORK_DOWNLOAD_URL = (
    "https://dotnet.microsoft.com/download/dotnet-framework/net48"
)


def _webview2_installation_guidance() -> tuple[str, str]:
    return (
        "Microsoft Edge WebView2 Runtime required",
        "PetroLumen could not start because the Microsoft Edge WebView2 Runtime "
        "is missing or unavailable. Install the Evergreen WebView2 Runtime, "
        "then restart PetroLumen:\n\n"
        f"{WEBVIEW2_DOWNLOAD_URL}",
    )


def _resource_path(relative_path: str) -> Path:
    bundle_root = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    )
    return bundle_root / relative_path


def _ensure_writable_directory(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=directory):
        pass


def _read_or_create_secret(secret_path: Path) -> str:
    try:
        secret_fd = os.open(
            secret_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        return secret_path.read_text(encoding="utf-8").strip()

    secret = secrets.token_urlsafe(48)
    with os.fdopen(secret_fd, "w", encoding="utf-8") as secret_file:
        secret_file.write(secret)
        secret_file.flush()
        os.fsync(secret_file.fileno())
    return secret


def _webview2_runtime_available() -> bool:
    if sys.platform != "win32":
        return True

    configured_folder = os.environ.get("WEBVIEW2_BROWSER_EXECUTABLE_FOLDER")
    if configured_folder and (
        Path(configured_folder) / "msedgewebview2.exe"
    ).is_file():
        return True

    runtime_roots = []
    for program_files in (
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramFiles"),
        os.environ.get("LOCALAPPDATA"),
    ):
        if program_files:
            runtime_roots.append(
                Path(program_files) / "Microsoft" / "EdgeWebView" / "Application"
            )
    return any(
        any(runtime_root.glob("*/msedgewebview2.exe"))
        for runtime_root in runtime_roots
    )


def _startup_error_guidance(exc: Exception) -> tuple[str, str] | None:
    error_text = f"{type(exc).__name__}: {exc}".casefold()
    if any(
        marker in error_text
        for marker in ("webview2", "edgechromium", "msedgewebview2", "webview2loader")
    ):
        return _webview2_installation_guidance()
    if any(
        marker in error_text
        for marker in (
            ".net",
            "net framework",
            "pythonnet",
            "python.runtime",
            "clr_loader",
            "no module named clr",
            "importing clr",
            "could not load file or assembly",
            "0x80131700",
        )
    ):
        return (
            ".NET Framework 4.8 required",
            "PetroLumen could not initialize its Windows desktop runtime. Install "
            "Microsoft .NET Framework 4.8, then restart PetroLumen:\n\n"
            f"{DOTNET_FRAMEWORK_DOWNLOAD_URL}",
        )
    return None


def _show_startup_dialog(title: str, message: str) -> None:
    from tkinter import messagebox

    messagebox.showerror(title, message)


def _configure_file_logging(data_dir: Path) -> tuple[logging.Handler, int]:
    log_dir = data_dir / "logs"
    _ensure_writable_directory(log_dir)
    handler = RotatingFileHandler(
        log_dir / "petrolumen.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )

    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.addHandler(handler)
    if root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)
    return handler, previous_level


def _configure_user_data() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        local_data_dir = Path(local_app_data) / "PetroLumen"
    elif sys.platform == "win32":
        local_data_dir = Path.home() / "AppData" / "Local" / "PetroLumen"
    else:
        local_data_dir = Path.home() / ".local" / "share" / "PetroLumen"

    candidates = [local_data_dir]
    if sys.platform == "win32":
        roaming_app_data = Path(
            os.environ.get("APPDATA")
            or Path.home() / "AppData" / "Roaming"
        )
        candidates.append(roaming_app_data / "PetroLumen")
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).resolve().parent / "data")
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidates.append(Path(meipass) / "data")
        candidates.append(Path(tempfile.gettempdir()) / "PetroLumen" / "data")

    unique_candidates = list(dict.fromkeys(candidates))
    failures: list[tuple[Path, OSError]] = []
    data_dir: Path | None = None
    secret: str | None = None
    for candidate in unique_candidates:
        try:
            _ensure_writable_directory(candidate)
            webview_dir = candidate / "webview"
            _ensure_writable_directory(webview_dir)
            _ensure_writable_directory(candidate / "logs")
            if "PETROLUMEN_SECRET_KEY" not in os.environ:
                secret = _read_or_create_secret(candidate / "secret.key")
        except OSError as exc:
            failures.append((candidate, exc))
            continue
        data_dir = candidate
        break

    if data_dir is None:
        failures_text = "; ".join(
            f"{path}: {error}" for path, error in failures
        )
        raise RuntimeError(
            f"Unable to create writable PetroLumen data directories: {failures_text}"
        ) from failures[-1][1]

    if failures:
        logger.warning(
            "Could not use earlier PetroLumen data directories; using %s after "
            "failures: %s",
            data_dir,
            "; ".join(f"{path}: {error}" for path, error in failures),
        )

    if secret is not None:
        if len(secret) < 32:
            raise RuntimeError(
                f"Authentication secret at {data_dir / 'secret.key'} is missing "
                "or invalid."
            )
        os.environ["PETROLUMEN_SECRET_KEY"] = secret

    database_path = data_dir / "petrolumen.db"
    os.environ.setdefault(
        "PETROLUMEN_DATABASE_URL",
        f"sqlite:///{database_path.resolve().as_posix()}",
    )

    return data_dir


class DesktopApi:
    def __init__(self, port: int) -> None:
        self._port = port

    def get_port(self) -> int:
        return self._port


def _shutdown_server(server: uvicorn.Server, server_thread: threading.Thread) -> None:
    server.should_exit = True
    server_thread.join(timeout=2)
    if server_thread.is_alive():
        logger.critical(
            "Embedded API did not stop within 2 seconds; terminating PetroLumen."
        )
        os._exit(0)


def main() -> None:
    if not _webview2_runtime_available():
        _show_startup_dialog(*_webview2_installation_guidance())
        return

    try:
        import webview
    except Exception as exc:
        guidance = _startup_error_guidance(exc)
        if guidance is None:
            raise
        _show_startup_dialog(*guidance)
        return

    user_data_dir = _configure_user_data()
    file_handler, previous_log_level = _configure_file_logging(user_data_dir)
    root_logger = logging.getLogger()
    try:
        _run_desktop_app(webview, user_data_dir)
    finally:
        root_logger.removeHandler(file_handler)
        file_handler.close()
        root_logger.setLevel(previous_log_level)


def _run_desktop_app(webview: ModuleType, user_data_dir: Path) -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    backend_path = _resource_path("backend")
    sys.path.insert(0, str(backend_path))

    from app.main import app
    from app.persistence.dependencies import initialize_database_manager

    initialize_database_manager(app)

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
    icon_path = _resource_path("public/petrolumen.ico")
    if not icon_path.is_file():
        raise FileNotFoundError(f"Desktop application icon not found at {icon_path}.")
    window = webview.create_window(
        "PetroLumen",
        f"http://127.0.0.1:{port}/ui/?{urlencode({'api_port': port})}",
        js_api=api,
        width=1280,
        height=850,
        min_size=(900, 600),
    )

    shutdown_lock = threading.Lock()
    shutdown_started = False

    def shutdown() -> None:
        nonlocal shutdown_started
        with shutdown_lock:
            if shutdown_started:
                return
            shutdown_started = True
        _shutdown_server(server, server_thread)

    window.events.closed += shutdown
    try:
        webview.start(
            icon=str(icon_path),
            private_mode=False,
            storage_path=str(user_data_dir / "webview"),
        )
    except Exception as exc:
        guidance = _startup_error_guidance(exc)
        if guidance is None:
            raise
        logger.exception("Desktop webview startup failed.")
        _show_startup_dialog(*guidance)
    finally:
        shutdown()


if __name__ == "__main__":
    main()
