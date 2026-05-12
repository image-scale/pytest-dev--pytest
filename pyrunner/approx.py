"""Approximate comparison utility for floating-point tolerance checks."""

import math
from collections.abc import Mapping, Sized
from decimal import Decimal


class ApproxValue:
    """Approximate comparison for a single numeric value."""

    RELATIVE_DEFAULT = 1e-6
    ABSOLUTE_DEFAULT = 1e-12

    def __init__(self, expected, rel=None, abs_tol=None, nan_ok=False):
        self.expected = expected
        self.rel = rel
        self.abs_tol = abs_tol
        self.nan_ok = nan_ok

    def __repr__(self):
        try:
            tol = self.tolerance
            if 1e-3 <= tol < 1e3:
                return f"{self.expected} ± {tol:g}"
            else:
                return f"{self.expected} ± {tol:.1e}"
        except (ValueError, TypeError):
            return f"{self.expected} ± ???"

    def __eq__(self, actual):
        if isinstance(self.expected, bool) or isinstance(actual, bool):
            if type(self.expected) is not type(actual):
                return False
            return self.expected == actual

        if not isinstance(self.expected, (int, float, complex, Decimal)):
            return self.expected == actual

        if not isinstance(actual, (int, float, complex, Decimal)):
            return False

        if isinstance(self.expected, complex) or isinstance(actual, complex):
            return self._complex_eq(actual)

        if math.isnan(float(self.expected)):
            return self.nan_ok and math.isnan(float(actual))

        if math.isinf(float(self.expected)):
            return self.expected == actual

        if self.expected == actual:
            return True

        return builtins_abs(self.expected - actual) <= self.tolerance

    def _complex_eq(self, actual):
        try:
            diff = builtins_abs(self.expected - actual)
        except TypeError:
            return False
        if math.isnan(diff):
            if self.nan_ok:
                return (math.isnan(self.expected.real) == math.isnan(actual.real) and
                        math.isnan(self.expected.imag) == math.isnan(actual.imag))
            return False
        return diff <= self.tolerance

    __hash__ = None

    def __ne__(self, actual):
        return not self.__eq__(actual)

    @property
    def tolerance(self):
        absolute = self.abs_tol if self.abs_tol is not None else self.ABSOLUTE_DEFAULT
        if absolute < 0:
            raise ValueError(f"absolute tolerance can't be negative: {absolute}")
        if isinstance(absolute, float) and math.isnan(absolute):
            raise ValueError("absolute tolerance can't be NaN")

        if self.rel is None and self.abs_tol is not None:
            return absolute

        rel_factor = self.rel if self.rel is not None else self.RELATIVE_DEFAULT
        try:
            relative = rel_factor * builtins_abs(self.expected)
        except TypeError:
            relative = 0

        if isinstance(relative, float) and relative < 0:
            raise ValueError(f"relative tolerance can't be negative: {relative}")
        if isinstance(relative, float) and math.isnan(relative):
            raise ValueError("relative tolerance can't be NaN")

        return max(relative, absolute)


class ApproxSequence:
    """Approximate comparison for sequences of numbers."""

    def __init__(self, expected, rel=None, abs_tol=None, nan_ok=False):
        self.expected = expected
        self.rel = rel
        self.abs_tol = abs_tol
        self.nan_ok = nan_ok

    def __repr__(self):
        items = [ApproxValue(x, self.rel, self.abs_tol, self.nan_ok) for x in self.expected]
        seq_type = type(self.expected)
        if seq_type not in (list, tuple):
            seq_type = list
        return f"approx({seq_type(items)!r})"

    def __eq__(self, actual):
        try:
            if len(actual) != len(self.expected):
                return False
        except TypeError:
            return False
        return all(
            ApproxValue(exp, self.rel, self.abs_tol, self.nan_ok) == act
            for exp, act in zip(self.expected, actual)
        )

    __hash__ = None

    def __ne__(self, actual):
        return not self.__eq__(actual)


class ApproxDict:
    """Approximate comparison for dictionary values."""

    def __init__(self, expected, rel=None, abs_tol=None, nan_ok=False):
        self.expected = expected
        self.rel = rel
        self.abs_tol = abs_tol
        self.nan_ok = nan_ok

    def __repr__(self):
        items = {
            k: ApproxValue(v, self.rel, self.abs_tol, self.nan_ok)
            for k, v in self.expected.items()
        }
        return f"approx({items!r})"

    def __eq__(self, actual):
        try:
            if set(actual.keys()) != set(self.expected.keys()):
                return False
        except AttributeError:
            return False
        return all(
            ApproxValue(self.expected[k], self.rel, self.abs_tol, self.nan_ok) == actual[k]
            for k in self.expected
        )

    __hash__ = None

    def __ne__(self, actual):
        return not self.__eq__(actual)


class ApproxDecimalValue(ApproxValue):
    """Approximate comparison for Decimal values."""

    RELATIVE_DEFAULT = Decimal("1e-6")
    ABSOLUTE_DEFAULT = Decimal("1e-12")


def approx(expected, rel=None, abs=None, nan_ok=False):
    """Create an approximate comparison object.

    Usage:
        assert 0.1 + 0.2 == approx(0.3)
        assert [0.1, 0.2] == approx([0.1, 0.2])
        assert {"a": 0.1} == approx({"a": 0.1})
    """
    if isinstance(expected, Decimal):
        return ApproxDecimalValue(expected, rel=rel, abs_tol=abs, nan_ok=nan_ok)
    elif isinstance(expected, Mapping):
        return ApproxDict(expected, rel=rel, abs_tol=abs, nan_ok=nan_ok)
    elif _is_sequence_like(expected):
        return ApproxSequence(expected, rel=rel, abs_tol=abs, nan_ok=nan_ok)
    else:
        return ApproxValue(expected, rel=rel, abs_tol=abs, nan_ok=nan_ok)


def _is_sequence_like(obj):
    return (
        hasattr(obj, "__getitem__")
        and isinstance(obj, Sized)
        and not isinstance(obj, (str, bytes))
    )


builtins_abs = abs
