"""Tests for test parametrization."""

import tempfile
import textwrap
from pathlib import Path

from pyrunner.parametrize import (
    parametrize,
    expand_parametrized,
    make_test_id,
    ParametrizeInfo,
    ParameterSet,
)
from pyrunner.runner import Session, Outcome


class TestParametrizeDecorator:

    def test_attaches_parametrize_marks(self):
        @parametrize("x", [1, 2, 3])
        def test_func(x):
            pass

        assert hasattr(test_func, '_parametrize_marks')
        assert len(test_func._parametrize_marks) == 1

    def test_multiple_parametrize_stacks(self):
        @parametrize("a", [1, 2])
        @parametrize("b", [10, 20])
        def test_func(a, b):
            pass

        assert len(test_func._parametrize_marks) == 2


class TestParametrizeInfo:

    def test_string_argnames(self):
        info = ParametrizeInfo("x,y", [(1, 2), (3, 4)])
        assert info.argnames == ["x", "y"]
        assert len(info.param_sets) == 2

    def test_list_argnames(self):
        info = ParametrizeInfo(["x", "y"], [(1, 2)])
        assert info.argnames == ["x", "y"]

    def test_single_param_scalar_values(self):
        info = ParametrizeInfo("x", [1, 2, 3])
        assert len(info.param_sets) == 3
        assert info.param_sets[0].values == (1,)
        assert info.param_sets[2].values == (3,)


class TestExpandParametrized:

    def test_non_parametrized_function(self):
        def test_plain():
            pass

        expanded = expand_parametrized(test_plain)
        assert len(expanded) == 1
        assert expanded[0][0] is None

    def test_single_param_expansion(self):
        @parametrize("x", [1, 2, 3])
        def test_vals(x):
            pass

        expanded = expand_parametrized(test_vals)
        assert len(expanded) == 3

    def test_expanded_functions_are_callable(self):
        results = []

        @parametrize("x", [10, 20])
        def test_collect(x):
            results.append(x)

        expanded = expand_parametrized(test_collect)
        for _, fn in expanded:
            fn()

        assert sorted(results) == [10, 20]

    def test_multi_param_expansion(self):
        @parametrize("a,b", [(1, 2), (3, 4)])
        def test_pair(a, b):
            pass

        expanded = expand_parametrized(test_pair)
        assert len(expanded) == 2

    def test_cartesian_product(self):
        @parametrize("a", [1, 2])
        @parametrize("b", [10, 20])
        def test_combo(a, b):
            pass

        expanded = expand_parametrized(test_combo)
        assert len(expanded) == 4

    def test_test_id_includes_values(self):
        @parametrize("x", [42])
        def test_with_id(x):
            pass

        expanded = expand_parametrized(test_with_id)
        param_id, _ = expanded[0]
        assert "42" in param_id


class TestMakeTestId:

    def test_no_param_id(self):
        assert make_test_id("test_foo", None) == "test_foo"

    def test_with_param_id(self):
        result = make_test_id("test_add", "1-2")
        assert result == "test_add[1-2]"


class TestRunnerParametrizeIntegration:

    def _make_session(self, tmpdir, code):
        tf = Path(tmpdir) / "test_param.py"
        tf.write_text(textwrap.dedent(code))
        return Session(paths=[tmpdir])

    def test_parametrized_test_runs_multiple_times(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.parametrize import parametrize

                @parametrize("x,expected", [(1, 1), (2, 4), (3, 9)])
                def test_square(x, expected):
                    assert x * x == expected
            """)
            session.run_all()
            code = session.summary()

            assert len(session.results) == 3
            assert all(r.outcome == Outcome.PASSED for r in session.results)
            assert code == 0

    def test_parametrized_with_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.parametrize import parametrize

                @parametrize("x", [1, 2, 3])
                def test_is_even(x):
                    assert x % 2 == 0
            """)
            session.run_all()
            code = session.summary()

            passed = sum(1 for r in session.results if r.outcome == Outcome.PASSED)
            failed = sum(1 for r in session.results if r.outcome == Outcome.FAILED)
            assert passed == 1
            assert failed == 2
            assert code == 1

    def test_parametrized_test_names_include_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.parametrize import parametrize

                @parametrize("val", [10, 20])
                def test_vals(val):
                    assert val > 0
            """)
            session.run_all()

            names = [r.name for r in session.results]
            assert any("10" in n for n in names)
            assert any("20" in n for n in names)

    def test_single_param_scalar_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.parametrize import parametrize

                @parametrize("word", ["hello", "world"])
                def test_words(word):
                    assert isinstance(word, str)
            """)
            session.run_all()
            assert len(session.results) == 2
            assert all(r.outcome == Outcome.PASSED for r in session.results)

    def test_cartesian_product_integration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.parametrize import parametrize

                @parametrize("x", [1, 2])
                @parametrize("y", [10, 20])
                def test_combo(x, y):
                    assert x + y > 0
            """)
            session.run_all()
            assert len(session.results) == 4
            assert all(r.outcome == Outcome.PASSED for r in session.results)
