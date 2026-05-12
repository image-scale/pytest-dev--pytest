"""Tests for test outcome control: skip, fail, xfail, skip_if, importorskip."""

import tempfile
import textwrap
from pathlib import Path

from pyrunner.outcomes import (
    skip,
    fail,
    xfail,
    skip_if,
    importorskip,
    Skipped,
    Failed,
    ExpectedFailure,
)
from pyrunner.runner import Session, Outcome


class TestSkipFunction:

    def test_skip_raises_test_skipped(self):
        try:
            skip("not ready")
            assert False, "skip() should have raised"
        except Skipped as e:
            assert e.reason == "not ready"

    def test_skip_with_empty_reason(self):
        try:
            skip()
            assert False
        except Skipped as e:
            assert e.reason == ""

    def test_skip_is_not_assertion_error(self):
        try:
            skip("reason")
        except Skipped:
            pass
        except AssertionError:
            assert False, "skip should not raise AssertionError"


class TestFailFunction:

    def test_fail_raises_test_failed(self):
        try:
            fail("explicit failure")
            assert False
        except Failed as e:
            assert e.reason == "explicit failure"

    def test_fail_with_empty_reason(self):
        try:
            fail()
        except Failed as e:
            assert e.reason == ""


class TestXfailFunction:

    def test_xfail_raises_expected_failure(self):
        try:
            xfail("known bug")
            assert False
        except ExpectedFailure as e:
            assert e.reason == "known bug"


class TestSkipIfFunction:

    def test_skip_if_true_raises(self):
        try:
            skip_if(True, "condition met")
            assert False
        except Skipped as e:
            assert e.reason == "condition met"

    def test_skip_if_false_does_not_raise(self):
        skip_if(False, "should not skip")

    def test_skip_if_with_expression(self):
        import sys
        try:
            skip_if(sys.platform != "nonexistent_os", "wrong platform")
            assert False
        except Skipped:
            pass


class TestImportorskip:

    def test_imports_existing_module(self):
        mod = importorskip("os")
        assert hasattr(mod, "path")

    def test_skips_missing_module(self):
        try:
            importorskip("nonexistent_module_xyz_123")
            assert False
        except Skipped as e:
            assert "nonexistent_module_xyz_123" in e.reason

    def test_custom_reason(self):
        try:
            importorskip("nonexistent_module_xyz_123", reason="need this lib")
            assert False
        except Skipped as e:
            assert "need this lib" in e.reason

    def test_minversion_satisfied(self):
        import os
        mod = importorskip("os")
        assert mod is os

    def test_minversion_too_high(self):
        try:
            importorskip("pyrunner", minversion="999.0.0")
            assert False
        except Skipped as e:
            assert "999.0.0" in e.reason


class TestRunnerIntegration:

    def _make_session(self, tmpdir, code):
        tf = Path(tmpdir) / "test_outcomes.py"
        tf.write_text(textwrap.dedent(code))
        return Session(paths=[tmpdir])

    def test_skip_counted_separately(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.outcomes import skip

                def test_skipped():
                    skip("not ready")

                def test_passes():
                    assert True
            """)
            session.run_all()
            code = session.summary()

            outcomes = [r.outcome for r in session.results]
            assert Outcome.SKIPPED in outcomes
            assert Outcome.PASSED in outcomes
            assert Outcome.FAILED not in outcomes
            assert code == 0

    def test_fail_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.outcomes import fail

                def test_explicit_fail():
                    fail("broken")
            """)
            session.run_all()
            code = session.summary()

            assert session.results[0].outcome == Outcome.FAILED
            assert code == 1

    def test_xfail_via_function_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.outcomes import xfail

                def test_expected_fail():
                    xfail("known bug")
                    assert False
            """)
            session.run_all()
            code = session.summary()

            assert session.results[0].outcome == Outcome.XFAIL
            assert code == 0

    def test_summary_includes_skipped_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.outcomes import skip

                def test_a():
                    skip("skip me")

                def test_b():
                    assert True
            """)
            session.run_all()
            session.summary()
            skipped_count = sum(1 for r in session.results if r.outcome == Outcome.SKIPPED)
            assert skipped_count == 1
