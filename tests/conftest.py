#!/usr/bin/env python3
import os
import shutil
import tempfile
from typing import Generator

from base import BaseTestcase
from base import ProjectInfo

import tomli
import tomli_w
import pytest


@pytest.fixture
def project_info() -> Generator[ProjectInfo, None, None]:
    """Yield a project directory with a cache set up."""
    with tempfile.TemporaryDirectory() as tmp_project_dir, tempfile.TemporaryDirectory() as tmp_cache_dir:
        project_name = os.path.basename(BaseTestcase.MY_PROJECT_DIR)
        project_dst = os.path.join(tmp_project_dir, project_name)
        shutil.copytree(BaseTestcase.MY_PROJECT_DIR, project_dst)

        tmp_cache_project_dir = os.path.join(tmp_cache_dir, project_name)
        shutil.copytree(BaseTestcase.MY_PROJECT_CACHE_DIR, tmp_cache_project_dir)

        # Adjust configuration to point to the cache directory.
        config_path = os.path.join(project_dst, ".virtualenv_cache.toml")
        with open(config_path, "rb") as f:
            config_content = tomli.load(f)

        config_content["virtualenv-cache"]["cache_path"] = tmp_cache_project_dir
        with open(config_path, "wb") as f:
            tomli_w.dump(config_content, f)

        yield ProjectInfo(
            project_dir=project_dst,
            cache_dir=tmp_cache_project_dir,
            config_path=config_path,
        )
