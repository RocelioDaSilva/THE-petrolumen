# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH).resolve()
BACKEND = ROOT / "backend"
FRONTEND_DIST = ROOT / "dist"
ENTRY_POINT = ROOT / "frontend_desktop" / "desktop_app.py"

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "vendor"))

hiddenimports = (
    ["app.main"]
    + collect_submodules("app.api")
    + collect_submodules("app.persistence")
    + [
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan.on",
        "webview.platforms.edgechromium",
        "webview.platforms.win32",
        "webview.platforms.winforms",
        "pythoncom",
        "pywintypes",
        "win32api",
        "win32con",
        "win32event",
        "win32gui",
        "win32timezone",
        "clr",
        "clr_loader",
        "pythonnet",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.dialects.sqlite.pysqlite",
        "lasio",
        "numpy",
        "pandas",
        "scipy",
        "scipy.linalg",
        "scipy.optimize",
        "scipy.sparse",
        "scipy.special",
        "sklearn",
        "sklearn.utils._cython_blas",
        "matplotlib",
        "matplotlib.backends.backend_agg",
        "numba",
        "llvmlite.binding",
    ]
)

backend_tree = Tree(
    str(BACKEND),
    prefix="backend",
    excludes=["tests", "__pycache__", ".venv", "venv", "*.pyc"],
)

datas = [
    (str(FRONTEND_DIST), "dist"),
    (str(ROOT / "public" / "petrolumen.ico"), "public"),
    (str(ROOT / "frontend_desktop" / "PetroLumen.exe.config"), "."),
    *[
        (source, str(Path(destination).parent))
        for destination, source, _typecode in backend_tree
    ],
    *collect_data_files("webview"),
]

a = Analysis(
    [str(ENTRY_POINT)],
    pathex=[str(BACKEND), str(BACKEND / "vendor")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["Agg"]}},
    runtime_hooks=[],
    excludes=["IPython", "pytest", "torch", "zmq"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PetroLumen",
    icon=str(ROOT / "public" / "petrolumen.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    contents_directory=".",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PetroLumen",
)
