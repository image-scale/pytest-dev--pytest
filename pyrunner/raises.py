"""Exception testing - context manager and callable form for verifying raised exceptions."""

import re
from types import TracebackType


class ExceptionDetails:
    """Holds information about a caught exception."""

    def __init__(self, exc_type, exc_value, exc_tb):
        self.type = exc_type
        self.value = exc_value
        self.tb = exc_tb

    def __repr__(self):
        return f"<ExceptionDetails {self.type.__name__}: {self.value}>"

    def __str__(self):
        return str(self.value)

    def match(self, pattern):
        """Check if the exception message matches the given regex pattern."""
        msg = str(self.value)
        if not re.search(pattern, msg):
            raise AssertionError(
                f"Regex pattern {pattern!r} did not match {msg!r}"
            )
        return True


class RaisesContext:
    """Context manager that asserts an exception is raised.

    Usage:
        with raises(ValueError) as exc_info:
            int("not a number")
        assert "invalid literal" in str(exc_info.value)
    """

    def __init__(self, expected_exception, match=None):
        if isinstance(expected_exception, type) and issubclass(expected_exception, BaseException):
            self.expected = (expected_exception,)
        elif isinstance(expected_exception, tuple):
            self.expected = expected_exception
        else:
            raise TypeError(
                f"expected an exception type or tuple, got {type(expected_exception)!r}"
            )
        self.match_pattern = match
        self.excinfo = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            expected_names = " or ".join(e.__name__ for e in self.expected)
            raise AssertionError(
                f"DID NOT RAISE {expected_names}"
            )

        if not issubclass(exc_type, self.expected):
            return False

        self.excinfo = ExceptionDetails(exc_type, exc_val, exc_tb)

        if self.match_pattern is not None:
            msg = str(exc_val)
            if not re.search(self.match_pattern, msg):
                raise AssertionError(
                    f"Regex pattern {self.match_pattern!r} did not match {msg!r}"
                )

        return True

    @property
    def value(self):
        if self.excinfo is None:
            raise AttributeError("No exception caught yet")
        return self.excinfo.value

    @property
    def type(self):
        if self.excinfo is None:
            raise AttributeError("No exception caught yet")
        return self.excinfo.type


def raises(expected_exception, func=None, *args, match=None, **kwargs):
    """Assert that a block of code or callable raises an expected exception.

    Can be used as a context manager:
        with raises(ValueError):
            int("abc")

    Or with a callable:
        raises(ValueError, int, "abc")
    """
    if func is not None:
        if not callable(func):
            raise TypeError(f"{func!r} is not callable")
        ctx = RaisesContext(expected_exception, match=match)
        try:
            func(*args, **kwargs)
        except BaseException:
            import sys
            exc_type, exc_val, exc_tb = sys.exc_info()
            if not ctx.__exit__(exc_type, exc_val, exc_tb):
                raise
            return ctx
        else:
            ctx.__exit__(None, None, None)

    return RaisesContext(expected_exception, match=match)
