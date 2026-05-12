"""Temporary directory fixtures for tests."""

import tempfile
from pathlib import Path
from shutil import rmtree

from pyrunner.fixtures import fixture, Scope


class TempPathFactory:
    """Factory for creating temporary directories under a common base."""

    def __init__(self, basetemp=None):
        self._basetemp = basetemp
        self._counter = 0

    def getbasetemp(self):
        if self._basetemp is None:
            self._basetemp = Path(tempfile.mkdtemp(prefix="pyrunner-"))
        return self._basetemp

    def mktemp(self, basename, numbered=True):
        base = self.getbasetemp()
        if numbered:
            p = base / f"{basename}{self._counter}"
            self._counter += 1
        else:
            p = base / basename
        p.mkdir(parents=True, exist_ok=True)
        return p

    def cleanup(self):
        if self._basetemp is not None and self._basetemp.exists():
            rmtree(self._basetemp, ignore_errors=True)
            self._basetemp = None


@fixture(scope="session")
def tmp_path_factory():
    factory = TempPathFactory()
    yield factory
    factory.cleanup()


@fixture
def tmp_path(tmp_path_factory):
    return tmp_path_factory.mktemp("test")
