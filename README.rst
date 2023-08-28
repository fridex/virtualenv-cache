virtualenv-cache
----------------

Manage a cache of virtual environments based on changes in requirements files.

An example usage of this tool might be a CI system that executes a testsuite.
If there are no changes in requirements, a cached virtual environment already
available in the CI might be used. This environment can have all the
dependencies already installed to speed up CI jobs.

If a new virtual environment is created, this virtual environment can be added
to the cache to speed up next CI jobs.

This tool automatically manages the cache, lifetime of cache entries, and
additional cache parameters based on the supplied configuration file.

Installation
============

You can install `the latest version from PyPI <https://pypi.org/project/virtualenv-cache>`__:

.. code-block:: console

  pip install virtualenv-cache

If you wish to run the latest version from `the Git repository <https://github.com/fridex/virtualenv-cache>`__:

.. code-block:: console

  pip install git+https://github.com/fridex/virtualenv-cache@latest

Usage
=====

First, there needs to be generated a configuration file:

.. code-block:: console

  virtualenv-cache init

The command above will create a configuration file in the current directory (by
default) called ``.virtualenv_cache.toml``. Check its configuration options as
described below to match your desired behavior. This file has be generated per
project that should be using the cache and should be part of the project code
base - e.g. committed to the Git repository so that it can be used on a clone.

Next, your configuration in a CI can look similar to the code snipped bellow:

.. code-block::

  cd project-root/
  virtualenv-cache restore
  [ $? -eq 1 ] && ( python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && virtualenv-cache store )

The code snipped above will try to restore a virtual environment from cache.
If there is no matching cached virtual environment, the ``restore`` command
exists with exit code of 1 indicating cache miss. In that case, the virtual
environment can be created and prepared for the next runs which will result in
a cache hit (unless there is a change in requirements files which results in a
new virtual environment creation that will get cached again). Just make sure
you keep all the requirements installed in your virtual environment and have
them stated in ``requirements_lock_paths``.

Configuration file
==================

The configuration file can be generated using ``virtualenv-cache init``. An
example of such configuration file:

.. code-block:: toml

  [virtualenv-cache]
  cache_size = 25
  cache_path = "${HOME}/.virtualenv-cache/my-project/cache/"
  virtualenv_path = ".venv"
  requirements_lock_paths = [
      "requirements.txt",
      "requirements-dev.txt",
      "requirements-typing.txt"
  ]

``cache_size``
##############

The number of virtual environments cached. If the ``cache_size`` is reached,
the cache is trimmed based on use of virtual environments - only the most used
virtual environments based on datetime are kept in the cache.

``cache_path``
##############

A path where cached virtual environments should be stored. If you use
``virtualenv-cache`` to manage cache for multiple projects, make sure you
define different ``cache_path`` for each of them.

The path configuration value can state environment variables which get
expanded.

``virtualenv_path``
###################

A path where the virtual environment is created for the project. This path is
used to copy the virtual environment into the cache or restored from the cache.

The path configuration value can state environment variables which get
expanded.

``requirements_lock_paths``
###########################

A list of requirements files that affect installed dependencies in the virtual
environment. There can be stated lock files, such as ``requirements.txt`` as
produced by `pip-tools <https://pypi.org/project/pip-tools/>`__, a
``poetry.lock`` file as produced by `Poetry <https://python-poetry.org/>`__, a
`pdm.lock <https://pdm.fming.dev/>`__ file as produced by `PDM
<https://pdm.fming.dev/>`__, or a ``Pipfile.lock`` as produced by `Pipenv
<https://github.com/pypa/pipenv>`__.

Note there are internally computed hashes of these files on their content
without taking into account semantics. That means any change, even a new line,
added to the file affects a new cache entry creation. Generally, this does not
create any issues as the old cache entries will get removed over time based on
the ``cache_size`` configuration option. This also mean that you can add any
other file which content potentially affects virtual environment to this
listing.

Commands
========

The tool can be run with the following sub-commands:

* ``virtualenv-cache store`` - store the curent virtual environment into the cache
* ``virtualenv-cache restore`` - restore the matching virtual environment from the cache
* ``virtualenv-cache init`` - initialize the configuration file
* ``virtualenv-cache list`` - list entries in the cache with their additional
  metadata, such as the last access time
* ``virtualenv-cache erase`` - drop all cached virtual environments

See ``--help`` for more information and options available.

Additional notes
================

All the CLI parameters can be supplied as environment variables:

* ``VIRTUALENV_CACHE_CONFIG_PATH`` - a path to the ``virtualenv-cache`` configuration file
* ``VIRTUALENV_CACHE_FORMAT`` - format used to print output to terminal
* ``VIRTUALENV_CACHE_WORK_DIR`` - a working directory for the CLI

