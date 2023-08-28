#!/usr/bin/env python3

import json
import logging
import os
import sys
from typing import Generator
from contextlib import contextmanager

import click
import daiquiri
from rich.console import Console
from rich.table import Table

from virtualenv_cache import Cache
from virtualenv_cache import Config
from virtualenv_cache import __title__
from virtualenv_cache import __version__
from virtualenv_cache import VirtualenvCacheException
from virtualenv_cache import VirtualenvCacheMiss

daiquiri.setup(level=logging.INFO)

_LOGGER = logging.getLogger(__title__)


@contextmanager
def cwd(target_dir: str | None) -> Generator[None, None, None]:
    """Work with directories in push/pop manner."""
    old_dir = os.getcwd()
    target_dir = target_dir or old_dir  # Noop on None.
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(old_dir)


@click.group()
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Run in verbose mode.",
)
def cli(verbose: bool = False) -> None:
    """Manage a cache of virtual environments respecting changes in requirements files."""
    if verbose:
        _LOGGER.setLevel(logging.DEBUG)
        _LOGGER.debug("Debug mode is on")


@cli.command()
def version() -> None:
    """Get version and exit."""
    click.echo(f"{__title__}: {__version__}")


@cli.command()
@click.option(
    "--config-path",
    "-c",
    type=str,
    default=Config.DEFAULT_CONFIG_PATH,
    metavar="CONFIG.toml",
    show_default=True,
    help="A path to the virtualenv-cache configuration file.",
    envvar="VIRTUALENV_CACHE_CONFIG_PATH",
)
@click.option(
    "--work-dir",
    "-w",
    type=str,
    default=os.getcwd(),
    metavar="DIR",
    show_default=True,
    help="Use the specified working directory as project root.",
)
def init(config_path: str, work_dir: str) -> None:
    """Initialize configuration file."""
    with cwd(work_dir):
        try:
            Config.create(config_path)
        except VirtualenvCacheException as exc:
            _LOGGER.error(str(exc))
            sys.exit(1)


@cli.command()
@click.option(
    "--config-path",
    "-c",
    type=str,
    default=Config.DEFAULT_CONFIG_PATH,
    metavar="CONFIG.toml",
    show_default=True,
    help="A path to the virtualenv-cache configuration file.",
    envvar="VIRTUALENV_CACHE_CONFIG_PATH",
)
@click.option(
    "--work-dir",
    "-w",
    type=str,
    default=os.getcwd(),
    metavar="DIR",
    show_default=True,
    help="Use the specified working directory as project root.",
)
def restore(config_path: str, work_dir: str) -> None:
    """Restore a Python environment from the cache.

    Check requirements files present in the project and pick a cached virtual environment, if available.
    If no virtual environment is available, signalize it with exit code 1 (cache miss).
    """
    with cwd(work_dir):
        try:
            config = Config.load(config_path)
            Cache(config=config).restore()
        except VirtualenvCacheMiss as exc:
            _LOGGER.error(str(exc))
            sys.exit(1)
        except Exception as exc:
            _LOGGER.exception(str(exc))
            sys.exit(2)


@cli.command()
@click.option(
    "--config-path",
    "-c",
    type=str,
    default=Config.DEFAULT_CONFIG_PATH,
    metavar="CONFIG.toml",
    show_default=True,
    help="A path to the virtualenv-cache configuration file.",
    envvar="VIRTUALENV_CACHE_CONFIG_PATH",
)
@click.option(
    "--work-dir",
    "-w",
    type=str,
    default=os.getcwd(),
    metavar="DIR",
    show_default=True,
    help="Use the specified working directory as project root.",
)
def store(config_path: str, work_dir: str) -> None:
    """Store the current state of virtual environment to the cache."""
    with cwd(work_dir):
        try:
            config = Config.load(config_path)
            Cache(config=config).store()
        except VirtualenvCacheException as exc:
            _LOGGER.error(str(exc))
            sys.exit(1)


@cli.command()
@click.option(
    "--config-path",
    "-c",
    type=str,
    default=Config.DEFAULT_CONFIG_PATH,
    metavar="CONFIG.toml",
    show_default=True,
    help="A path to the virtualenv-cache configuration file.",
    envvar="VIRTUALENV_CACHE_CONFIG_PATH",
)
@click.option(
    "--work-dir",
    "-w",
    type=str,
    default=os.getcwd(),
    metavar="DIR",
    show_default=True,
    help="Use the specified working directory as project root.",
)
def erase(config_path: str, work_dir: str) -> None:
    """Erase the cache."""
    with cwd(work_dir):
        try:
            config = Config.load(config_path)
            Cache(config=config).erase()
        except VirtualenvCacheException as exc:
            _LOGGER.error(str(exc))
            sys.exit(1)


@cli.command("list")
@click.option(
    "--config-path",
    "-c",
    type=str,
    default=Config.DEFAULT_CONFIG_PATH,
    metavar="CONFIG.toml",
    show_default=True,
    help="A path to the virtualenv-cache configuration file.",
    envvar="VIRTUALENV_CACHE_CONFIG_PATH",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    metavar="FMT",
    show_default=True,
    help="Format used to list environments.",
)
@click.option(
    "--work-dir",
    "-w",
    type=str,
    default=os.getcwd(),
    metavar="DIR",
    show_default=True,
    help="Use the specified working directory as project root.",
)
def list_(config_path: str, format: str, work_dir: str) -> None:
    """List available cached virtual environments."""
    with cwd(work_dir):
        try:
            config = Config.load(config_path)
            result = Cache(config=config).list()
        except VirtualenvCacheException as exc:
            _LOGGER.error(str(exc))
            sys.exit(1)

        if format == "table":
            if not result:
                return

            table = Table(title="Cached Python environments")

            table.add_column("ID", justify="center", style="cyan", no_wrap=True)
            table.add_column("Hostname", style="magenta")
            table.add_column("Last used", justify="left", style="green")

            for entry in result:
                table.add_row(entry["id"], entry["hostname"], entry["datetime"])

            console = Console()
            console.print(table)
        elif format == "json":
            json.dump(result, sys.stdout, sort_keys=True, indent=2)
            click.echo("\n")
        else:
            raise NotImplementedError(f"Unknown output format {format!r}")


__name__ == "__main__" and cli()
