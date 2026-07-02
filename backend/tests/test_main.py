import os
from pathlib import Path

import main


def test_load_env_file_populates_missing_env_vars(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "already-set")

    env_file = tmp_path / ".env"
    env_file.write_text(
        "OLLAMA_API_KEY=test-key\nOLLAMA_MODEL=from-file\n# COMMENT=ignored\n",
        encoding="utf-8",
    )

    main.load_env_file(env_file)

    assert os.getenv("OLLAMA_API_KEY") == "test-key"
    assert os.getenv("OLLAMA_MODEL") == "already-set"


def test_load_env_file_ignores_missing_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    missing_env_file = tmp_path / ".env"
    main.load_env_file(missing_env_file)

    assert os.getenv("OLLAMA_API_KEY") is None
