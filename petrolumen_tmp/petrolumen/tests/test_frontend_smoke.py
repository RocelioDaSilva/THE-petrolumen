import os
import urllib.request
import urllib.error

import pytest


def test_status_component_file_exists():
    path = os.path.join("app", "components", "StatusOverview.tsx")
    assert os.path.exists(path), f"Missing component file: {path}"


def _http_get(url, timeout=2):
    req = urllib.request.Request(url, headers={"User-Agent": "pytest-smoke"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8"), r.getcode()


def test_next_dev_root_contains_status():
    url = "http://127.0.0.1:3000/"
    try:
        body, code = _http_get(url, timeout=2)
    except Exception:
        pytest.skip("Next dev server not running at http://127.0.0.1:3000")

    assert code == 200
    assert ("PetroLúmen" in body) or ("Petroleum" in body)
    assert ("Simulações concluídas hoje" in body) or ("Simulações" in body)


def test_standalone_bundle_present():
    # Check that a standalone next bundle was placed into the tauri bundle resources
    root = os.path.join("src-tauri", "bundle", "resources", "next")
    assert os.path.exists(root), f"Standalone Next bundle not found at {root}"

    server_js = os.path.join(root, "server.js")
    assert os.path.exists(server_js), "server.js missing in standalone Next bundle"

    node_next = os.path.join(root, "node_modules", "next")
    assert os.path.exists(node_next), "Bundled node_modules/next missing in standalone Next bundle"
