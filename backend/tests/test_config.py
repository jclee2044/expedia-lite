"""Checks for project-root environment configuration."""

from pathlib import Path

import pytest

import backend.config as config


@pytest.mark.parametrize("contents", [None, "", "GEOAPIFY_API_KEY=   \n"])
def test_geoapify_key_is_not_configured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contents: str | None,
) -> None:
    env_file = tmp_path / ".env"
    if contents is not None:
        env_file.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)

    assert config.geoapify_key_is_configured() is False


def test_geoapify_key_is_configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("GEOAPIFY_API_KEY=synthetic-test-value\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)

    assert config.get_geoapify_api_key() == "synthetic-test-value"
    assert config.geoapify_key_is_configured() is True
