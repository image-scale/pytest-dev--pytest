"""Stdout/stderr capture for tests."""

import sys
import io
from collections import namedtuple

from pyrunner.fixtures import fixture

CaptureResult = namedtuple("CaptureResult", ["out", "err"])


class CaptureFixture:
    """Captures writes to sys.stdout and sys.stderr."""

    def __init__(self):
        self._capture_out = None
        self._capture_err = None
        self._original_out = None
        self._original_err = None
        self._captured_out = ""
        self._captured_err = ""

    def _start(self):
        self._original_out = sys.stdout
        self._original_err = sys.stderr
        self._capture_out = io.StringIO()
        self._capture_err = io.StringIO()
        sys.stdout = self._capture_out
        sys.stderr = self._capture_err

    def close(self):
        if self._original_out is not None:
            self._captured_out += self._capture_out.getvalue()
            self._captured_err += self._capture_err.getvalue()
            sys.stdout = self._original_out
            sys.stderr = self._original_err
            self._original_out = None
            self._original_err = None

    def readouterr(self):
        out = self._captured_out
        err = self._captured_err
        if self._capture_out is not None:
            out += self._capture_out.getvalue()
            err += self._capture_err.getvalue()
            self._capture_out.truncate(0)
            self._capture_out.seek(0)
            self._capture_err.truncate(0)
            self._capture_err.seek(0)
        self._captured_out = ""
        self._captured_err = ""
        return CaptureResult(out, err)

    def disabled(self):
        return _CaptureDisabled(self)


class _CaptureDisabled:
    def __init__(self, cap):
        self._cap = cap

    def __enter__(self):
        if self._cap._original_out is not None:
            self._cap._captured_out += self._cap._capture_out.getvalue()
            self._cap._captured_err += self._cap._capture_err.getvalue()
            self._cap._capture_out.truncate(0)
            self._cap._capture_out.seek(0)
            self._cap._capture_err.truncate(0)
            self._cap._capture_err.seek(0)
            sys.stdout = self._cap._original_out
            sys.stderr = self._cap._original_err

    def __exit__(self, *args):
        if self._cap._original_out is not None:
            sys.stdout = self._cap._capture_out
            sys.stderr = self._cap._capture_err


@fixture
def capsys():
    cap = CaptureFixture()
    cap._start()
    yield cap
    cap.close()
