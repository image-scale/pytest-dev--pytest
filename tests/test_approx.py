"""Tests for approximate floating-point comparisons."""

import math
from decimal import Decimal

from pyrunner.approx import approx, ApproxValue, ApproxSequence, ApproxDict


class TestApproxScalar:

    def test_exact_equality(self):
        assert 1.0 == approx(1.0)

    def test_close_values(self):
        assert 0.1 + 0.2 == approx(0.3)

    def test_not_close_values(self):
        assert not (1.0 == approx(2.0))

    def test_custom_relative_tolerance(self):
        assert 1.001 == approx(1.0, rel=1e-2)
        assert not (1.1 == approx(1.0, rel=1e-3))

    def test_custom_absolute_tolerance(self):
        assert 1.0001 == approx(1.0, abs=1e-3)
        assert not (1.01 == approx(1.0, abs=1e-3))

    def test_abs_only_ignores_relative(self):
        assert not (1 + 1e-8 == approx(1, abs=1e-12))

    def test_both_rel_and_abs(self):
        assert 1 + 1e-8 == approx(1, rel=1e-6, abs=1e-12)

    def test_zero_expected(self):
        assert 1e-13 == approx(0.0)
        assert not (1e-6 == approx(0.0))

    def test_infinity_equals_itself(self):
        assert math.inf == approx(math.inf)
        assert -math.inf == approx(-math.inf)

    def test_infinity_not_equal_to_finite(self):
        assert not (1e300 == approx(math.inf))

    def test_nan_not_equal_by_default(self):
        assert not (math.nan == approx(math.nan))

    def test_nan_equal_with_nan_ok(self):
        assert math.nan == approx(math.nan, nan_ok=True)

    def test_negative_tolerance_raises(self):
        try:
            _ = ApproxValue(1.0, abs_tol=-1).tolerance
            assert False
        except ValueError:
            pass

    def test_integer_comparison(self):
        assert 10 == approx(10)
        assert not (10 == approx(11))

    def test_bool_not_equal_to_int(self):
        assert not (1 == approx(True))
        assert not (0 == approx(False))
        assert True == approx(True)
        assert False == approx(False)

    def test_repr(self):
        r = repr(approx(1.0))
        assert "1.0" in r
        assert "±" in r

    def test_ne_operator(self):
        assert 1.0 != approx(2.0)
        assert not (1.0 != approx(1.0))

    def test_non_numeric_fallback_to_strict(self):
        assert "hello" == approx("hello")
        assert not ("hello" == approx("world"))

    def test_none_comparison(self):
        assert None == approx(None)
        assert not (None == approx(1))


class TestApproxSequence:

    def test_equal_lists(self):
        assert [0.1 + 0.2, 0.2 + 0.4] == approx([0.3, 0.6])

    def test_unequal_lists(self):
        assert not ([1.0, 2.0, 3.0] == approx([1.0, 2.0, 4.0]))

    def test_different_lengths(self):
        assert not ([1.0, 2.0] == approx([1.0]))

    def test_tuples(self):
        assert (0.1 + 0.2, 0.2 + 0.4) == approx((0.3, 0.6))

    def test_sequence_with_tolerance(self):
        assert [1.001, 2.001] == approx([1.0, 2.0], rel=1e-2)

    def test_nested_list_not_supported_as_flat(self):
        assert [1.0, 2.0, 3.0] == approx([1.0, 2.0, 3.0])


class TestApproxDict:

    def test_equal_dicts(self):
        assert {"a": 0.1 + 0.2, "b": 0.2 + 0.4} == approx({"a": 0.3, "b": 0.6})

    def test_unequal_dicts(self):
        assert not ({"a": 1.0} == approx({"a": 2.0}))

    def test_different_keys(self):
        assert not ({"a": 1.0} == approx({"b": 1.0}))

    def test_dict_with_tolerance(self):
        assert {"x": 1.001} == approx({"x": 1.0}, rel=1e-2)

    def test_dict_with_none_values(self):
        assert {"required": 1.0000005, "optional": None} == approx(
            {"required": 1, "optional": None}
        )


class TestApproxDecimal:

    def test_decimal_comparison(self):
        assert Decimal("0.3") == approx(Decimal("0.3"))

    def test_decimal_close_values(self):
        assert Decimal("1.0000001") == approx(Decimal("1.0"), rel=Decimal("1e-5"))


class TestApproxComplex:

    def test_complex_equal(self):
        assert (1 + 2j) == approx(1 + 2j)

    def test_complex_close(self):
        assert (1.0000001 + 2j) == approx(1 + 2j)

    def test_complex_not_close(self):
        assert not ((1 + 2j) == approx(3 + 4j))
