#!/usr/bin/env python3

import datetime
import hashlib
import json
import logging
import os
import shutil
import socket
from typing import Any
from typing import Dict
from typing import List

import attr
from dateutil.parser import parse as parse_datetime

from ._config import Config
from ._exceptions import VirtualenvCacheMiss
from ._exceptions import VirtualenvCacheConfigError

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Cache:
    """A cache for Python virtual environments."""

    _CACHE_ENTRY_USAGE_FILE = "virtualenv-cache-usage.json"

    config = attr.ib(type=Config, kw_only=True)

    def _hash_all_lock_files(self) -> str:
        """Retrieve a hash of all the lock files."""
        file_hashes = {}
        if not self.config.requirements_lock_paths:
            _LOGGER.warning(
                "No requirements lock files defined in the configuration file"
            )

        for item in self.config.requirements_lock_paths:
            _LOGGER.debug("Computing hash for requirements lock file %r", item)
            try:
                with open(item, "rb") as f:
                    sha256_hash = hashlib.sha256(f.read()).hexdigest()
            except FileNotFoundError as exc:
                raise VirtualenvCacheConfigError(
                    f"File {item!r} stated in the configuration file not found"
                ) from exc

            file_hashes[item] = sha256_hash

        return hashlib.sha256(
            json.dumps(file_hashes, sort_keys=True).encode()
        ).hexdigest()

    def _mark_cache_entry_usage(self, cached_entry_path: str) -> None:
        """Mark usage of the given cached virtual environment."""
        content = {
            "hostname": socket.gethostname(),
            "datetime": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        }
        with open(
            os.path.join(cached_entry_path, self._CACHE_ENTRY_USAGE_FILE), "w"
        ) as f:
            json.dump(content, f)

    def _get_cache_entry_usage(self, cached_entry_path: str) -> Dict[str, Any]:
        """Get usage of the given file."""
        usage_file_path = os.path.join(cached_entry_path, self._CACHE_ENTRY_USAGE_FILE)
        with open(usage_file_path) as f:
            content = json.load(f)

        return content

    def _list_entries(self) -> List[Dict[str, Any]]:
        """List entries stored in the cache, sorted by usage."""
        result = []
        for entry in os.listdir(self.config.expanded_cache_path):
            entry_path = os.path.join(self.config.expanded_cache_path, entry)
            if not os.path.isdir(entry_path):
                continue

            record = self._get_cache_entry_usage(entry_path)
            record["id"] = entry
            result.append(record)

        result.sort(key=lambda x: parse_datetime(x["datetime"]), reverse=True)
        return result

    def _trim_cache(self) -> None:
        """Remove entries from the cache respecting the cache size configuration."""
        entries = self._list_entries()
        if self.config.cache_size >= len(entries):
            _LOGGER.debug(
                "Nothing to be removed from the cache, cache size %d out of %d",
                len(entries),
                self.config.cache_size,
            )
            return

        for to_drop in entries[self.config.cache_size :]:
            _LOGGER.info(
                "Removing cached entry to match expected cache size %d: %r",
                self.config.cache_size,
                to_drop["id"],
            )
            shutil.rmtree(os.path.join(self.config.expanded_cache_path, to_drop["id"]))

    def restore(self) -> None:
        """Check already existing cached virtual environment and make it available, if possible."""
        _LOGGER.debug("Calculating digests of requirements files")
        all_hashed = self._hash_all_lock_files()
        _LOGGER.debug("Calculated hash of all the lock files: %s", all_hashed)

        cached_entry_path = os.path.join(self.config.expanded_cache_path, all_hashed)
        if not os.path.exists(cached_entry_path):
            raise VirtualenvCacheMiss("No cached virtual environment found")

        # Remove any virtual environment already present.
        _LOGGER.info(
            "Restoring virtual environment from cache %r to %r",
            cached_entry_path,
            self.config.expanded_virtualenv_path,
        )
        shutil.rmtree(self.config.expanded_virtualenv_path, ignore_errors=True)
        shutil.copytree(
            os.path.join(cached_entry_path, "venv"),
            self.config.expanded_virtualenv_path,
        )

        self._mark_cache_entry_usage(cached_entry_path)

    def store(self) -> None:
        """Store any changes done to the virtual environment and make them available for the next round."""
        all_hashed = self._hash_all_lock_files()
        cached_entry_path = os.path.join(self.config.expanded_cache_path, all_hashed)

        os.makedirs(cached_entry_path, exist_ok=True)

        _LOGGER.info(
            "Storing virtual environment %r to cache in %r",
            self.config.expanded_virtualenv_path,
            cached_entry_path,
        )
        cached_venv_path = os.path.join(cached_entry_path, "venv")
        shutil.rmtree(cached_venv_path, ignore_errors=True)
        shutil.copytree(self.config.expanded_virtualenv_path, cached_venv_path)

        self._mark_cache_entry_usage(cached_entry_path)
        self._trim_cache()

    def list(self) -> List[Dict[str, Any]]:
        """List all the environments available."""
        if not os.path.isdir(self.config.expanded_cache_path):
            _LOGGER.warning("The configured cache hasn't been used yet")
            return []

        return self._list_entries()

    def erase(self) -> None:
        """Erase the cache."""
        if os.path.exists(self.config.expanded_cache_path):
            _LOGGER.warning(
                "Erasing cache located in %r", self.config.expanded_cache_path
            )
            shutil.rmtree(self.config.expanded_cache_path)
        else:
            _LOGGER.warning("No cache in %r found", self.config.expanded_cache_path)
