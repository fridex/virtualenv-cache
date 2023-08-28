#!/usr/bin/env python3

import os
import json
from typing import Any
from typing import Dict

import pytest
from click.testing import CliRunner
from virtualenv_cache.cli import cli
from virtualenv_cache import __title__
from virtualenv_cache import __version__

from base import BaseTestcase


class TestCLI(BaseTestcase):
    """Tests related to the CLI."""

    def test_help(self) -> None:
        """Test printing the help message."""
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: ")

    def test_version(self) -> None:
        """Test printing tool version."""
        result = CliRunner().invoke(cli, ["version"])
        assert result.exit_code == 0
        assert result.output == f"{__title__}: {__version__}\n"

    @pytest.mark.parametrize(
        "project_dir, output",
        [
            pytest.param(
                BaseTestcase.MY_PROJECT_DIR,
                [
                    {
                        "datetime": "2023-08-28T18:08:13.486841+00:00",
                        "hostname": "masina",
                        "id": "18648aedbe40f5e25f2fe09f80295ed1a4bc996d1b47fb8d24c4f08a6e565b47",
                    },
                    {
                        "datetime": "2023-08-28T18:07:56.370582+00:00",
                        "hostname": "masina",
                        "id": "b824faa77c86dd2019ef176a3be4af21b02274a7680c44fc75a6606421918154",
                    },
                ],
            ),
            pytest.param(BaseTestcase.EMPTY_PROJECT_DIR, []),
        ],
    )
    def test_list(self, project_dir: str, output: Dict[str, Any]) -> None:
        """Test listing entries in the cache."""
        config_path = os.path.join(project_dir, ".virtualenv_cache.toml")
        result = CliRunner().invoke(
            cli,
            [
                "list",
                "--work-dir",
                project_dir,
                "--config-path",
                config_path,
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == output

    def test_restore(self) -> None:
        """Test restoring a virtual environment."""
        # TODO: implement

    def test_store(self) -> None:
        """Test storing a virtual environment in the cache."""
        # TODO: implement

    def test_erase(self) -> None:
        """Test erasing the cache."""
        # TODO: implement

    def test_init(self) -> None:
        """Test initializing the cache."""
        # TODO: implement
