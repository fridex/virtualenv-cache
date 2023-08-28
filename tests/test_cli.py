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
from base import ProjectInfo


class TestCLI(BaseTestcase):
    """Tests related to the CLI."""

    def test_help(self) -> None:
        """Test printing the help message."""
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: ")

        result = CliRunner().invoke(cli, [])
        assert result.exit_code == 0
        assert result.output.startswith("Usage: ")

    def test_version(self) -> None:
        """Test printing tool version."""
        result = CliRunner().invoke(cli, ["version"])
        assert result.exit_code == 0
        assert result.output == f"{__title__}: {__version__}\n"

    @pytest.mark.parametrize(
        "my_project_dir, output",
        [
            pytest.param(
                BaseTestcase.MY_PROJECT_DIR,
                [
                    {
                        "datetime": "2023-08-28T18:18:13.486841+00:00",
                        "hostname": "masina",
                        "id": "6f741140d80b32fc7fc72313e411569f5af412e8f9e30ae1bc52ac0837157435",
                    },
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
    def test_list(self, my_project_dir: str, output: Dict[str, Any]) -> None:
        """Test listing entries in the cache."""
        config_path = os.path.join(my_project_dir, ".virtualenv_cache.toml")
        result = CliRunner().invoke(
            cli,
            [
                "list",
                "--work-dir",
                my_project_dir,
                "--config-path",
                config_path,
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == output

    def test_restore(self, project_info: ProjectInfo) -> None:
        """Test restoring a virtual environment."""
        assert ".venv" not in os.listdir(project_info.project_dir)
        result = CliRunner().invoke(
            cli,
            [
                "restore",
                "--work-dir",
                project_info.project_dir,
                "--config-path",
                project_info.config_path,
            ],
        )
        assert ".venv" in os.listdir(project_info.project_dir)
        assert result.exit_code == 0

    def test_store(self, project_info: ProjectInfo) -> None:
        """Test storing a virtual environment in the cache."""
        assert ".venv" not in os.listdir(project_info.project_dir)

        result = CliRunner().invoke(
            cli,
            [
                "restore",
                "--work-dir",
                project_info.project_dir,
                "--config-path",
                project_info.config_path,
            ],
        )
        assert result.exit_code == 0
        assert ".venv" in os.listdir(project_info.project_dir)

    def test_erase(self, project_info: ProjectInfo) -> None:
        """Test erasing the cache."""
        assert len(os.listdir(project_info.cache_dir)) >= 1

        result = CliRunner().invoke(
            cli,
            [
                "erase",
                "--work-dir",
                project_info.project_dir,
                "--config-path",
                project_info.config_path,
            ],
        )

        assert result.exit_code == 0
        assert not os.path.exists(project_info.cache_dir)

    def test_init(self, tmpdir: str) -> None:
        """Test initializing the cache."""
        config_file_name = ".virtualenv_cache.toml"
        config_path = os.path.join(tmpdir, config_file_name)

        result = CliRunner().invoke(
            cli,
            ["init", "--work-dir", tmpdir, "--config-path", config_path],
        )

        assert result.exit_code == 0
        assert config_file_name in os.listdir(tmpdir)
