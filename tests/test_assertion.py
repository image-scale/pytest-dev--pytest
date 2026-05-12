"""Tests for assertion introspection and formatting."""

from pyrunner.assertion import (
    format_comparison,
    format_unary,
    introspect_assertion,
    _string_diff,
    _sequence_diff,
    _dict_diff,
)


class TestFormatComparison:

    def test_equality_shows_both_values(self):
        msg = format_comparison(1, 2, "==")
        assert "1" in msg
        assert "2" in msg
        assert "==" in msg

    def test_inequality_shows_equal_values(self):
        msg = format_comparison(5, 5, "!=")
        assert "!=" in msg
        assert "Both sides are equal" in msg

    def test_greater_than(self):
        msg = format_comparison(3, 5, ">")
        assert "3" in msg
        assert "5" in msg
        assert "not greater than" in msg

    def test_greater_equal(self):
        msg = format_comparison(2, 5, ">=")
        assert "not greater than or equal to" in msg

    def test_less_than(self):
        msg = format_comparison(5, 3, "<")
        assert "not less than" in msg

    def test_less_equal(self):
        msg = format_comparison(5, 3, "<=")
        assert "not less than or equal to" in msg

    def test_in_operator(self):
        msg = format_comparison("x", [1, 2, 3], "in")
        assert "'x'" in msg
        assert "not found" in msg

    def test_not_in_operator(self):
        msg = format_comparison(1, [1, 2, 3], "not in")
        assert "unexpectedly found" in msg

    def test_is_operator(self):
        msg = format_comparison([], [], "is")
        assert "is not" in msg

    def test_is_not_operator(self):
        a = []
        msg = format_comparison(a, a, "is not")
        assert "same object" in msg

    def test_string_diff_for_long_strings(self):
        left = "a" * 30 + "X" + "b" * 30
        right = "a" * 30 + "Y" + "b" * 30
        msg = format_comparison(left, right, "==")
        assert "==" in msg

    def test_function_return_value_comparison(self):
        def compute():
            return 42
        result = compute()
        msg = format_comparison(result, 99, "==")
        assert "42" in msg
        assert "99" in msg


class TestFormatUnary:

    def test_not_with_truthy_value(self):
        msg = format_unary(True, "not")
        assert "not" in msg
        assert "truthy" in msg

    def test_not_with_list(self):
        msg = format_unary([1, 2, 3], "not")
        assert "not" in msg
        assert "truthy" in msg


class TestStringDiff:

    def test_short_strings_no_diff(self):
        result = _string_diff("abc", "def")
        assert result == []

    def test_long_strings_show_diff(self):
        left = "line1\nline2\nline3\nline4\n" * 2
        right = "line1\nlineX\nline3\nline4\n" * 2
        result = _string_diff(left, right)
        assert len(result) > 0
        assert any("Diff" in line for line in result)


class TestSequenceDiff:

    def test_different_lengths(self):
        result = _sequence_diff([1, 2, 3], [1, 2])
        assert any("Length mismatch" in line for line in result)

    def test_first_differing_element(self):
        result = _sequence_diff([1, 2, 3], [1, 9, 3])
        assert any("index 1" in line for line in result)

    def test_same_prefix_different_length(self):
        result = _sequence_diff([1, 2], [1, 2, 3])
        assert any("extra" in line for line in result)


class TestDictDiff:

    def test_missing_keys(self):
        result = _dict_diff({"a": 1, "b": 2}, {"a": 1, "c": 3})
        assert any("only in left" in line.lower() for line in result)
        assert any("only in right" in line.lower() for line in result)

    def test_differing_values(self):
        result = _dict_diff({"a": 1, "b": 2}, {"a": 1, "b": 99})
        assert any("Differing" in line for line in result)
        assert any("99" in line for line in result)

    def test_equal_dicts_no_diff(self):
        result = _dict_diff({"a": 1}, {"a": 1})
        assert result == []


class TestIntrospectAssertion:

    def _capture_tb(self, func):
        """Helper that runs func() and returns the traceback if it raises AssertionError."""
        import sys
        try:
            func()
        except AssertionError:
            return sys.exc_info()[2]
        return None

    def test_integration_with_comparison(self):
        import sys
        a = 10
        b = 20
        try:
            assert a == b
        except AssertionError:
            tb = sys.exc_info()[2]
            msg = introspect_assertion(tb)
            assert msg is not None
            assert "10" in msg
            assert "20" in msg

    def test_integration_with_in_operator(self):
        import sys
        item = "z"
        container = ["a", "b", "c"]
        try:
            assert item in container
        except AssertionError:
            tb = sys.exc_info()[2]
            msg = introspect_assertion(tb)
            assert msg is not None
            assert "'z'" in msg

    def test_integration_with_not(self):
        import sys
        value = [1, 2, 3]
        try:
            assert not value
        except AssertionError:
            tb = sys.exc_info()[2]
            msg = introspect_assertion(tb)
            assert msg is not None
            assert "not" in msg

    def test_integration_with_greater_than(self):
        import sys
        a = 5
        b = 10
        try:
            assert a > b
        except AssertionError:
            tb = sys.exc_info()[2]
            msg = introspect_assertion(tb)
            assert msg is not None
            assert "5" in msg
            assert "10" in msg

    def test_integration_with_is(self):
        import sys
        a = []
        b = []
        try:
            assert a is b
        except AssertionError:
            tb = sys.exc_info()[2]
            msg = introspect_assertion(tb)
            assert msg is not None
            assert "is not" in msg
