"""Tests for warning testing utilities."""

import warnings

from pyrunner.warn_utils import warns, deprecated_call, WarningRecorder, WarningChecker


class TestWarns:

    def test_catches_expected_warning(self):
        with warns(UserWarning):
            warnings.warn("test warning", UserWarning)

    def test_fails_if_no_warning(self):
        try:
            with warns(UserWarning):
                pass
            assert False
        except AssertionError as e:
            assert "DID NOT WARN" in str(e)

    def test_match_pattern(self):
        with warns(UserWarning, match=r"important"):
            warnings.warn("this is important", UserWarning)

    def test_match_pattern_fails(self):
        try:
            with warns(UserWarning, match=r"missing"):
                warnings.warn("something else", UserWarning)
            assert False
        except AssertionError as e:
            assert "did not match" in str(e).lower()

    def test_multiple_warnings(self):
        with warns(UserWarning) as recorder:
            warnings.warn("first", UserWarning)
            warnings.warn("second", UserWarning)
        assert len(recorder) == 2

    def test_specific_warning_subclass(self):
        with warns(DeprecationWarning):
            warnings.warn("old api", DeprecationWarning)

    def test_wrong_warning_type(self):
        try:
            with warns(DeprecationWarning):
                warnings.warn("user warning", UserWarning)
            assert False
        except AssertionError as e:
            assert "DID NOT WARN" in str(e)

    def test_tuple_of_warning_types(self):
        with warns((UserWarning, DeprecationWarning)):
            warnings.warn("old", DeprecationWarning)

    def test_callable_form(self):
        def emit_warning():
            warnings.warn("callable warning", UserWarning)

        recorder = warns(UserWarning, emit_warning)
        assert len(recorder) >= 1

    def test_access_warning_message(self):
        with warns(UserWarning) as recorder:
            warnings.warn("check this", UserWarning)
        assert "check this" in str(recorder[0].message)

    def test_subclass_warning_caught(self):
        with warns(Warning):
            warnings.warn("general", UserWarning)


class TestDeprecatedCall:

    def test_catches_deprecation_warning(self):
        with deprecated_call():
            warnings.warn("use new api", DeprecationWarning)

    def test_catches_pending_deprecation(self):
        with deprecated_call():
            warnings.warn("will be removed", PendingDeprecationWarning)

    def test_catches_future_warning(self):
        with deprecated_call():
            warnings.warn("future change", FutureWarning)

    def test_fails_without_deprecation(self):
        try:
            with deprecated_call():
                pass
            assert False
        except AssertionError:
            pass

    def test_callable_form(self):
        def old_api():
            warnings.warn("deprecated", DeprecationWarning)

        deprecated_call(old_api)

    def test_with_match(self):
        with deprecated_call(match=r"use.*v2"):
            warnings.warn("use new v2 api", DeprecationWarning)


class TestWarningRecorder:

    def test_records_multiple_types(self):
        with WarningRecorder() as rec:
            warnings.warn("user", UserWarning)
            warnings.warn("runtime", RuntimeWarning)
        assert len(rec) == 2

    def test_pop_by_category(self):
        with WarningRecorder() as rec:
            warnings.warn("user", UserWarning)
            warnings.warn("runtime", RuntimeWarning)
        popped = rec.pop(RuntimeWarning)
        assert popped.category is RuntimeWarning
        assert len(rec) == 1

    def test_pop_not_found(self):
        with WarningRecorder() as rec:
            warnings.warn("user", UserWarning)
        try:
            rec.pop(DeprecationWarning)
            assert False
        except AssertionError:
            pass

    def test_clear(self):
        with WarningRecorder() as rec:
            warnings.warn("test", UserWarning)
        assert len(rec) > 0
        rec.clear()
        assert len(rec) == 0

    def test_iter(self):
        with WarningRecorder() as rec:
            warnings.warn("a", UserWarning)
            warnings.warn("b", UserWarning)
        messages = [str(w.message) for w in rec]
        assert "a" in messages
        assert "b" in messages

    def test_cannot_enter_twice(self):
        rec = WarningRecorder()
        with rec:
            try:
                with rec:
                    pass
                assert False
            except RuntimeError:
                pass
