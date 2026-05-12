"""Tests for the test runner module."""

import os
import tempfile
import textwrap
from pathlib import Path
from io import StringIO
import sys

from pyrunner.runner import Session, Outcome, RunResult, run_tests


class TestRunResult:

    def test_passed_result(self):
        r = RunResult("test_foo.py", "test_add", Outcome.PASSED, 0.01)
        assert r.outcome == Outcome.PASSED
        assert r.name == "test_add"
        assert r.filepath == "test_foo.py"

    def test_failed_result(self):
        exc = AssertionError("expected 1 got 2")
        r = RunResult("test_foo.py", "test_sub", Outcome.FAILED, 0.02, exc)
        assert r.outcome == Outcome.FAILED
        assert r.exception is exc

    def test_node_id(self):
        r = RunResult("tests/test_math.py", "test_add", Outcome.PASSED)
        assert r.node_id == "tests/test_math.py::test_add"

    def test_node_id_without_name(self):
        r = RunResult("tests/test_math.py", None, Outcome.ERROR)
        assert r.node_id == "tests/test_math.py"


class TestSession:

    def _make_test_dir(self, tmpdir, code):
        tf = Path(tmpdir) / "test_sample.py"
        tf.write_text(textwrap.dedent(code))
        return tmpdir

    def test_all_passing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_test_dir(tmpdir, """\
                def test_one():
                    assert True

                def test_two():
                    assert 1 + 1 == 2
            """)

            session = Session(paths=[tmpdir])
            session.run_all()
            code = session.summary()

            passed = [r for r in session.results if r.outcome == Outcome.PASSED]
            assert len(passed) == 2
            assert code == 0

    def test_with_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_test_dir(tmpdir, """\
                def test_ok():
                    assert True

                def test_bad():
                    assert 1 == 2
            """)

            session = Session(paths=[tmpdir])
            session.run_all()
            code = session.summary()

            failed = [r for r in session.results if r.outcome == Outcome.FAILED]
            assert len(failed) == 1
            assert code == 1

    def test_with_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_test_dir(tmpdir, """\
                def test_error():
                    raise RuntimeError("boom")
            """)

            session = Session(paths=[tmpdir])
            session.run_all()

            errors = [r for r in session.results if r.outcome == Outcome.ERROR]
            assert len(errors) == 1
            assert "boom" in str(errors[0].exception)

    def test_assertion_error_is_failure_not_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_test_dir(tmpdir, """\
                def test_assert_fail():
                    assert False, "this should fail"
            """)

            session = Session(paths=[tmpdir])
            session.run_all()

            failed = [r for r in session.results if r.outcome == Outcome.FAILED]
            errors = [r for r in session.results if r.outcome == Outcome.ERROR]
            assert len(failed) == 1
            assert len(errors) == 0

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = Session(paths=[tmpdir])
            session.run_all()
            code = session.summary()
            assert len(session.results) == 0
            assert code == 0

    def test_results_have_duration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_test_dir(tmpdir, """\
                def test_quick():
                    pass
            """)

            session = Session(paths=[tmpdir])
            session.run_all()
            assert session.results[0].duration >= 0

    def test_handles_import_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_bad_import.py"
            tf.write_text("import this_module_does_not_exist_xyz\n")

            session = Session(paths=[tmpdir])
            session.run_all()
            code = session.summary()

            errors = [r for r in session.results if r.outcome == Outcome.ERROR]
            assert len(errors) == 1
            assert code == 1

    def test_recursive_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subpkg"
            subdir.mkdir()
            (Path(tmpdir) / "test_top.py").write_text("def test_a(): pass\n")
            (subdir / "test_deep.py").write_text("def test_b(): pass\n")

            session = Session(paths=[tmpdir])
            session.run_all()

            names = [r.name for r in session.results]
            assert "test_a" in names
            assert "test_b" in names

    def test_specific_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "test_one.py"
            f1.write_text("def test_x(): pass\n")
            f2 = Path(tmpdir) / "test_two.py"
            f2.write_text("def test_y(): pass\n")

            session = Session(paths=[str(f1)])
            session.run_all()

            names = [r.name for r in session.results]
            assert "test_x" in names
            assert "test_y" not in names


class TestRunTests:

    def test_returns_zero_on_all_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_ok.py"
            tf.write_text("def test_pass(): assert True\n")
            code = run_tests(paths=[tmpdir])
            assert code == 0

    def test_returns_one_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_fail.py"
            tf.write_text("def test_fail(): assert False\n")
            code = run_tests(paths=[tmpdir])
            assert code == 1

    def test_mixed_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_mixed.py"
            tf.write_text(textwrap.dedent("""\
                def test_ok(): assert True
                def test_bad(): assert False
            """))
            code = run_tests(paths=[tmpdir])
            assert code == 1
