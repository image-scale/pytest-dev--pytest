"""Test outcome control - skip, fail, xfail, and related utilities."""

import importlib
import sys
import warnings


class Skipped(Exception):
    """Raised when a test is skipped."""
    def __init__(self, reason=""):
        self.reason = reason
        super().__init__(reason)


class Failed(Exception):
    """Raised for explicit test failure."""
    def __init__(self, reason=""):
        self.reason = reason
        super().__init__(reason)


class ExpectedFailure(Exception):
    """Raised when a test is expected to fail."""
    def __init__(self, reason=""):
        self.reason = reason
        super().__init__(reason)


def skip(reason=""):
    """Skip the currently executing test with the given reason."""
    raise Skipped(reason)


def fail(reason=""):
    """Explicitly fail the currently executing test with the given reason."""
    raise Failed(reason)


def xfail(reason=""):
    """Mark the currently executing test as expected to fail."""
    raise ExpectedFailure(reason)


def skip_if(condition, reason=""):
    """Skip the test if the condition is true."""
    if condition:
        raise Skipped(reason)


def importorskip(modname, minversion=None, reason=None):
    """Import and return the module, or skip the test if import fails.

    If minversion is given, the module's __version__ must be at least that.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = importlib.import_module(modname)
    except ImportError:
        if reason is None:
            reason = f"could not import {modname!r}"
        raise Skipped(reason)

    if minversion is not None:
        ver = getattr(mod, "__version__", None)
        if ver is None:
            raise Skipped(
                f"module {modname!r} has no __version__, required: {minversion!r}"
            )
        from packaging.version import Version
        if Version(ver) < Version(minversion):
            raise Skipped(
                f"module {modname!r} has version {ver!r}, required: {minversion!r}"
            )

    return mod
