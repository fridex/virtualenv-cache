#!/usr/bin/env python3

import os

import attr
import pytest
from base import BaseTestcase

from virtualenv_cache import Config
from virtualenv_cache import VirtualenvCacheConfigError


class TestConfig(BaseTestcase):
    """Tests related to the configuration file."""

    def test_create(self, tmpdir: str) -> None:
        """Test creating a configuration file with defaults."""
        config_path = os.path.join(tmpdir, "myconf.toml")
        config_created = Config.create(config_path)
        config_loaded = Config.load(config_path)
        config_default = Config()

        assert attr.asdict(config_created) == attr.asdict(config_loaded)
        assert attr.asdict(config_created) == attr.asdict(config_default)

    def test_load(self, tmpdir: str) -> None:
        """Test loading a configuration file."""
        content = """\
[virtualenv-cache]
cache_size = 10
cache_path = "/foo/bar"
virtualenv_path = "my-venv"
requirements_lock_paths = [
  "requirements.txt",
  "requirements-dev.txt",
  "requirements-stage.txt",
]"""
        config_path = os.path.join(tmpdir, "myconf.toml")
        with open(config_path, "w") as f:
            f.write(content)

        config = Config.load(config_path)

        assert config.cache_size == 10
        assert config.cache_path == "/foo/bar"
        assert config.virtualenv_path == "my-venv"
        assert set(config.requirements_lock_paths) == {
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-stage.txt",
        }

    def test_load_non_existing(self) -> None:
        """Test loading a non-existing config is raising an exception."""
        with pytest.raises(
            VirtualenvCacheConfigError,
            match="^Configuration file '/some-non-existing-path' not found$",
        ):
            Config.load("/some-non-existing-path")

    def test_expand_cache_path(self) -> None:
        """Test expanding cache path based on environment variables."""
        config = Config()
        config.cache_path = "${PWD}"
        assert config.expanded_cache_path == os.getcwd()

    def test_virtualenv_path(self) -> None:
        """Test expanding virtualenv path based on environment variables."""
        config = Config()

        config.virtualenv_path = "${PWD}"
        assert config.expanded_virtualenv_path == os.getcwd()
