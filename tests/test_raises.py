"""Tests for the exception testing context manager."""

from pyrunner.raises import raises, RaisesContext, ExceptionDetails


class TestRaisesContextManager:

    def test_catches_expected_exception(self):
        with raises(ValueError):
            raise ValueError("bad value")

    def test_fails_if_no_exception(self):
        try:
            with raises(ValueError):
                pass
            assert False, "should have raised AssertionError"
        except AssertionError as e:
            assert "DID NOT RAISE" in str(e)

    def test_does_not_catch_wrong_exception(self):
        try:
            with raises(ValueError):
                raise TypeError("wrong type")
            assert False
        except TypeError:
            pass

    def test_provides_exception_info(self):
        with raises(ValueError) as exc_info:
            raise ValueError("test message")
        assert exc_info.value is not None
        assert "test message" in str(exc_info.value)
        assert exc_info.type is ValueError

    def test_match_pattern(self):
        with raises(ValueError, match=r"invalid.*value"):
            raise ValueError("invalid input value")

    def test_match_pattern_fails(self):
        try:
            with raises(ValueError, match=r"missing"):
                raise ValueError("wrong message")
            assert False
        except AssertionError as e:
            assert "did not match" in str(e).lower()

    def test_tuple_of_exceptions(self):
        with raises((ValueError, TypeError)):
            raise TypeError("type error")

    def test_tuple_catches_first_type(self):
        with raises((ValueError, TypeError)):
            raise ValueError("value error")

    def test_subclass_caught(self):
        with raises(Exception):
            raise ValueError("subclass of Exception")


class TestRaisesCallable:

    def test_callable_form(self):
        ctx = raises(ValueError, int, "abc")
        assert ctx.excinfo is not None
        assert ctx.type is ValueError

    def test_callable_form_no_raise(self):
        try:
            raises(ValueError, int, "42")
            assert False
        except AssertionError as e:
            assert "DID NOT RAISE" in str(e)

    def test_callable_with_match(self):
        ctx = raises(ValueError, int, "abc", match=r"invalid literal")
        assert ctx.excinfo is not None

    def test_callable_wrong_exception(self):
        try:
            raises(TypeError, int, "abc")
            assert False
        except ValueError:
            pass


class TestExceptionDetails:

    def test_repr(self):
        info = ExceptionDetails(ValueError, ValueError("oops"), None)
        r = repr(info)
        assert "ValueError" in r
        assert "oops" in r

    def test_str(self):
        info = ExceptionDetails(ValueError, ValueError("oops"), None)
        assert str(info) == "oops"

    def test_match_success(self):
        info = ExceptionDetails(ValueError, ValueError("invalid input"), None)
        assert info.match(r"invalid")

    def test_match_failure(self):
        info = ExceptionDetails(ValueError, ValueError("bad input"), None)
        try:
            info.match(r"missing")
            assert False
        except AssertionError:
            pass


class TestRaisesInvalidUsage:

    def test_non_exception_type_raises_type_error(self):
        try:
            raises("not an exception type")
            assert False
        except TypeError:
            pass

    def test_non_callable_raises_type_error(self):
        try:
            raises(ValueError, "not callable")
            assert False
        except TypeError:
            pass
