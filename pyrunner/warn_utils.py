"""Warning testing - context managers for asserting warnings are emitted."""

import re
import warnings
from collections.abc import Iterator


class WarningRecorder(warnings.catch_warnings):
    """Context manager that records warnings emitted during a block.

    Provides list-like access to recorded warning messages.
    """

    def __init__(self):
        super().__init__(record=True)
        self._records = []
        self._active = False

    @property
    def records(self):
        return self._records

    def __getitem__(self, index):
        return self._records[index]

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)

    def pop(self, cls=Warning):
        """Pop the first warning matching the given category."""
        for i, w in enumerate(self._records):
            if issubclass(w.category, cls):
                return self._records.pop(i)
        raise AssertionError(f"{cls!r} not found in warning list")

    def clear(self):
        self._records.clear()

    def __enter__(self):
        if self._active:
            raise RuntimeError("Cannot enter WarningRecorder twice")
        result = super().__enter__()
        assert result is not None
        self._records = result
        self._active = True
        warnings.simplefilter("always")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self._active = False
        return None


class WarningChecker(WarningRecorder):
    """Context manager that asserts specific warning types are emitted."""

    def __init__(self, expected_warning=Warning, match=None):
        super().__init__()
        if isinstance(expected_warning, type) and issubclass(expected_warning, Warning):
            self.expected = (expected_warning,)
        elif isinstance(expected_warning, tuple):
            for w in expected_warning:
                if not (isinstance(w, type) and issubclass(w, Warning)):
                    raise TypeError(f"expected warning type, got {type(w)}")
            self.expected = expected_warning
        else:
            raise TypeError(f"expected warning type or tuple, got {type(expected_warning)}")
        self.match_pattern = match

    def _matches(self, warning_record):
        """Check if a warning record matches expected type and pattern."""
        if not issubclass(warning_record.category, self.expected):
            return False
        if self.match_pattern is not None:
            return bool(re.search(self.match_pattern, str(warning_record.message)))
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

        if exc_val is not None and not isinstance(exc_val, Exception):
            return None

        if not any(issubclass(w.category, self.expected) for w in self._records):
            expected_names = ", ".join(e.__name__ for e in self.expected)
            found = [str(w.message) for w in self._records]
            raise AssertionError(
                f"DID NOT WARN. No warnings of type ({expected_names}) were emitted. "
                f"Emitted warnings: {found}"
            )

        if self.match_pattern is not None:
            if not any(self._matches(w) for w in self._records):
                raise AssertionError(
                    f"Regex pattern {self.match_pattern!r} did not match any of the "
                    f"{len(self._records)} warnings emitted."
                )

        for w in self._records:
            if not self._matches(w):
                warnings.warn_explicit(
                    message=w.message,
                    category=w.category,
                    filename=w.filename,
                    lineno=w.lineno,
                )

        return None


def warns(expected_warning=Warning, func=None, *args, match=None, **kwargs):
    """Assert that code emits a warning of the expected type.

    Can be used as context manager:
        with warns(UserWarning):
            warnings.warn("something", UserWarning)

    Or with a callable:
        warns(UserWarning, my_func, arg1, arg2)
    """
    if func is not None:
        if not callable(func):
            raise TypeError(f"{func!r} is not callable")
        with WarningChecker(expected_warning, match=match) as recorder:
            func(*args, **kwargs)
        return recorder

    return WarningChecker(expected_warning, match=match)


def deprecated_call(func=None, *args, match=None, **kwargs):
    """Assert that code produces a DeprecationWarning, PendingDeprecationWarning, or FutureWarning.

    Can be used as context manager:
        with deprecated_call():
            old_api()

    Or with a callable:
        deprecated_call(old_api, arg1)
    """
    deprecation_types = (DeprecationWarning, PendingDeprecationWarning, FutureWarning)
    if func is not None:
        return warns(deprecation_types, func, *args, match=match, **kwargs)
    return warns(deprecation_types, match=match)
