from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULES_TO_CLEAR = [
    "main",
    "routers.export",
    "routers.generate",
    "routers.styles",
    "services.export",
    "services.generate",
    "services.styles",
    "services.embeddings",
    "database.db",
    "providers.anthropic",
    "providers.ollama",
    "providers.registry",
]


def _install_dependency_stubs(monkeypatch) -> None:
    fake_sentence_transformers = types.ModuleType("sentence_transformers")

    class FakeSentenceTransformer:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def encode(self, text: str):
            return [float(len(text))]

    fake_sentence_transformers.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_sentence_transformers)

    fake_sqlite_vec = types.ModuleType("sqlite_vec")
    fake_sqlite_vec.load = lambda _conn: None
    monkeypatch.setitem(sys.modules, "sqlite_vec", fake_sqlite_vec)

    fake_anthropic = types.ModuleType("anthropic")

    class FakeAsyncAnthropic:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fake_anthropic.AsyncAnthropic = FakeAsyncAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)


def _import_main(monkeypatch):
    _install_dependency_stubs(monkeypatch)
    monkeypatch.syspath_prepend(str(BACKEND_DIR))

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    return importlib.import_module("main")


def test_main_import_registers_active_routes(monkeypatch):
    module = _import_main(monkeypatch)

    paths = {route.path for route in module.app.routes}

    assert "/health" in paths
    assert "/generate" in paths
    assert "/generations" in paths
    assert "/generations/{generation_id}" in paths
    assert "/styles" in paths
    assert "/styles/{style_id}" in paths
    assert "/export" in paths
    assert "/test" in paths


def test_app_startup_initializes_database_from_existing_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path))
    module = _import_main(monkeypatch)

    with TestClient(module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert (tmp_path / "gpt-writer.db").exists()


def test_preexisting_styles_router_is_reachable(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path))
    module = _import_main(monkeypatch)

    with TestClient(module.app) as client:
        response = client.get("/styles")

    assert response.status_code == 200
    assert response.json() == []
