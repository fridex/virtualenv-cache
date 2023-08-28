#!/usr/bin/env python3

import logging
import os.path
import pathlib
from typing import List

import attr
import tomli
from pathlib import Path

from ._exceptions import VirtualenvCacheConfigError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Config:
    """A configuration file stating information about Python projects virtualenv."""

    DEFAULT_CONFIG_PATH = str(Path().cwd() / ".virtualenv_cache.toml")
    _DEFAULT_CONFIG_CONTENT_PATH = str(
        pathlib.Path(__file__).parent.resolve()
        / "data"
        / "default_virtualenv_cache.toml.template"
    )

    cache_size = attr.ib(type=int, default=20)
    cache_path = attr.ib(
        type=str,
        default=os.path.join(
            "${HOME}/.virtualenv_cache/caches/", os.path.basename(os.getcwd())
        ),
    )
    virtualenv_path = attr.ib(type=str, default=".venv", kw_only=True)
    requirements_lock_paths = attr.ib(
        type=List[str], default=attr.Factory(list), kw_only=True
    )

    @property
    def expanded_cache_path(self) -> str:
        """Expand any environment variables stored in the `cache_path` configuration option."""
        return os.path.expandvars(self.cache_path)

    @property
    def expanded_virtualenv_path(self) -> str:
        """Expand any environment variables stored in the `virtualenv_path` configuration option."""
        return os.path.expandvars(self.virtualenv_path)

    @classmethod
    def create(cls, config_path: str) -> "Config":
        """Create a configuration file and write it to the given path."""
        _LOGGER.warning("Creating initial configuration file in %r", config_path)
        if os.path.isfile(config_path):
            raise VirtualenvCacheConfigError(
                f"Configuration file {config_path!r} already exists"
            )

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(cls._DEFAULT_CONFIG_CONTENT_PATH) as f:
            config_content = f.read()

        # Create a config instance with defaults.
        config = Config()
        if os.path.exists(config.expanded_cache_path):
            _LOGGER.warning(
                "Found already existing cache entries in %r, please make sure there is no clash with other "
                "projects and eventually adjust the `cache_path' configuration entry in your configuration file",
                config.expanded_cache_path,
            )

        config_content = config_content.format(**attr.asdict(config))

        _LOGGER.info("Writing initial configuration file to %r", config_path)
        with open(config_path, "w") as f:
            f.write(config_content)

        return config

    @classmethod
    def load(cls, config_path: str) -> "Config":
        """Load a configuration file from the given location."""
        _LOGGER.debug("Loading configuration file from %r", config_path)
        if not os.path.isfile(config_path):
            raise VirtualenvCacheConfigError(
                f"Configuration file {config_path!r} not found"
            )

        with open(config_path, "rb") as f:
            content = tomli.load(f)
            _LOGGER.debug("Config file content: %r", content)

        config = Config()
        config.requirements_lock_paths.clear()
        for k, v in content["virtualenv-cache"].items():
            _LOGGER.debug("Setting configuration %s=%s", k, v)
            if isinstance(v, list):
                for item in v:
                    getattr(config, k).append(item)
            else:
                setattr(config, k, v)

        return config
