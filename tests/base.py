#!/usr/bin/env python3

import os


class BaseTestcase:
    """A base class for implementing tests."""

    _DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    EMPTY_PROJECT_CACHE_DIR = os.path.join(_DATA_DIR, "caches", "empty-project")
    MY_PROJECT_CACHE_DIR = os.path.join(_DATA_DIR, "caches", "my-project")
    EMPTY_PROJECT_DIR = os.path.join(_DATA_DIR, "projects", "empty-project")
    MY_PROJECT_DIR = os.path.join(_DATA_DIR, "projects", "my-project")
