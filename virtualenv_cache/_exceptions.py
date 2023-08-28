#!/usr/bin/env python3


class VirtualenvCacheException(Exception):
    """A base class in the exceptions hierarchy for implementing exceptions."""


class VirtualenvCacheMiss(VirtualenvCacheException):
    """An exception raised when there is no matching entry in the cache."""


class VirtualenvCacheConfigError(VirtualenvCacheException):
    """An exception raised on an issue with a configuration file."""
