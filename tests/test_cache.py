#!/usr/bin/env python3
import datetime
import os
import hashlib
import json
import socket
from dateutil.parser import parse as parse_datetime

from base import BaseTestcase

import pytest
from virtualenv_cache import Cache
from virtualenv_cache import Config
from virtualenv_cache import VirtualenvCacheMiss
from virtualenv_cache.utils import cwd

from base import ProjectInfo


class TestCache(BaseTestcase):
    """Tests related to the cache."""

    def test_hash_all_lock_files(self) -> None:
        """Test hashing lock files present in the configuration file."""
        config = Config()
        cache = Cache(config=config)
        assert config.requirements_lock_paths == []
        assert (
            cache._hash_all_lock_files()
            == hashlib.sha256(json.dumps({}).encode()).hexdigest()
        )

    def test_cache_entry_usage(self, project_info: ProjectInfo) -> None:
        """Test marking and retrieving a cache entry usage."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)

        project_cache_dir = os.path.join(project_info.cache_dir, "foo")
        os.makedirs(project_cache_dir)
        cache._mark_cache_entry_usage(project_cache_dir)

        content = cache._get_cache_entry_usage(project_cache_dir)

        assert set(content.keys()) == {"hostname", "datetime"}
        assert content["hostname"] == socket.gethostname()
        assert content["datetime"] is not None
        dt = parse_datetime(content["datetime"])
        assert dt <= datetime.datetime.now(tz=datetime.timezone.utc)

    def test_list_entries(self, project_info: ProjectInfo) -> None:
        """Test listing entries stored in a cache."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)
        assert cache._list_entries() == [
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
        ]

    def test_trim_cache(self, project_info: ProjectInfo) -> None:
        """Test trimming a cache."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)
        config.cache_size = 1
        cache._trim_cache()
        assert cache._list_entries() == [
            {
                "datetime": "2023-08-28T18:18:13.486841+00:00",
                "hostname": "masina",
                "id": "6f741140d80b32fc7fc72313e411569f5af412e8f9e30ae1bc52ac0837157435",
            }
        ]

    def test_restore_cache_miss(self, project_info: ProjectInfo) -> None:
        """Test a cache miss on restore."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)

        assert ".venv" not in os.listdir(project_info.project_dir)

        # Adjust one of the lock files to make sure we have a cache miss.
        with open(
            os.path.join(project_info.project_dir, config.requirements_lock_paths[0]),
            "w",
        ) as f:
            f.write("requests>=1.1.0\n")

        with cwd(project_info.project_dir), pytest.raises(
            VirtualenvCacheMiss, match="^No cached virtual environment found$"
        ):
            cache.restore()

    def test_restore(self, project_info: ProjectInfo) -> None:
        """Test a cache miss error."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)

        assert ".venv" not in os.listdir(project_info.project_dir)
        with cwd(project_info.project_dir):
            cache.restore()
        assert ".venv" in os.listdir(project_info.project_dir)

    def test_store(self, project_info: ProjectInfo) -> None:
        """Test storing a cached entry."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)

        venv_path = os.path.join(project_info.project_dir, ".venv")
        os.makedirs(venv_path)

        with open(
            os.path.join(project_info.project_dir, config.requirements_lock_paths[0]),
            "w",
        ) as f:
            f.write("requests>=1.1.0\n")

        with cwd(project_info.project_dir):
            cache.store()

        expected_hash = (
            "d2cea636000de2a95d1653cc9beecba0e09f1c7a735d857008b9f339e3583aee"
        )
        assert expected_hash in os.listdir(project_info.cache_dir)
        assert "venv" in os.listdir(os.path.join(project_info.cache_dir, expected_hash))

    def test_list(self, project_info: ProjectInfo) -> None:
        """Test listing all the cache entries."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)
        assert cache._list_entries() == [
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
        ]

    def test_erase(self, project_info: ProjectInfo) -> None:
        """Test erasing a cache."""
        config = Config.load(project_info.config_path)
        cache = Cache(config=config)

        assert len(os.listdir(project_info.cache_dir)) > 0
        with cwd(project_info.project_dir):
            cache.erase()
        assert not os.path.exists(project_info.cache_dir)
