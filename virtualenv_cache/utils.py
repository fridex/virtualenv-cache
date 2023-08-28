#!/usr/bin/env python3

import os
from typing import Generator
from typing import Optional
from contextlib import contextmanager


@contextmanager
def cwd(target_dir: Optional[str]) -> Generator[None, None, None]:
    """Work with directories in push/pop manner."""
    old_dir = os.getcwd()
    target_dir = target_dir or old_dir  # Noop on None.
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(old_dir)
