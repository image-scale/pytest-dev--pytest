"""Tests for the fixture system."""

import tempfile
import textwrap
from pathlib import Path

from pyrunner.fixtures import fixture, FixtureManager, Scope, FixtureDefinition
from pyrunner.runner import Session, Outcome


class TestFixtureDecorator:

    def test_bare_decorator(self):
        @fixture
        def my_data():
            return [1, 2, 3]

        assert hasattr(my_data, '_fixture_definition')
        assert my_data._fixture_definition.name == "my_data"
        assert my_data._fixture_definition.scope == Scope.FUNCTION

    def test_decorator_with_scope(self):
        @fixture(scope="module")
        def shared_data():
            return {"key": "value"}

        assert shared_data._fixture_definition.scope == Scope.MODULE

    def test_decorator_with_autouse(self):
        @fixture(autouse=True)
        def auto_setup():
            return "auto"

        assert auto_setup._fixture_definition.autouse is True

    def test_decorator_with_custom_name(self):
        @fixture(name="custom")
        def my_func():
            return 42

        assert my_func._fixture_definition.name == "custom"

    def test_generator_fixture_detected(self):
        @fixture
        def gen_fixture():
            yield "value"

        assert gen_fixture._fixture_definition.is_generator is True

    def test_non_generator_fixture(self):
        @fixture
        def regular():
            return 1

        assert regular._fixture_definition.is_generator is False


class TestFixtureManager:

    def test_register_and_resolve(self):
        mgr = FixtureManager()

        @fixture
        def data():
            return [1, 2, 3]

        mgr.register(data._fixture_definition)
        result = mgr.resolve("data")
        assert result == [1, 2, 3]

    def test_generator_fixture_setup_teardown(self):
        teardown_called = []

        @fixture
        def resource():
            obj = {"created": True}
            yield obj
            teardown_called.append(True)

        mgr = FixtureManager()
        mgr.register(resource._fixture_definition)

        val = mgr.resolve("resource")
        assert val == {"created": True}
        assert teardown_called == []

        mgr.teardown_function()
        assert teardown_called == [True]

    def test_fixture_dependencies(self):
        @fixture
        def base_val():
            return 10

        @fixture
        def derived(base_val):
            return base_val * 2

        mgr = FixtureManager()
        mgr.register(base_val._fixture_definition)
        mgr.register(derived._fixture_definition)

        val = mgr.resolve("derived")
        assert val == 20

    def test_function_scope_cache(self):
        call_count = []

        @fixture
        def counted():
            call_count.append(1)
            return len(call_count)

        mgr = FixtureManager()
        mgr.register(counted._fixture_definition)

        v1 = mgr.resolve("counted")
        v2 = mgr.resolve("counted")
        assert v1 == v2 == 1

        mgr.teardown_function()

        v3 = mgr.resolve("counted")
        assert v3 == 2

    def test_module_scope_survives_function_teardown(self):
        call_count = []

        @fixture(scope="module")
        def mod_data():
            call_count.append(1)
            return len(call_count)

        mgr = FixtureManager()
        mgr.register(mod_data._fixture_definition)

        v1 = mgr.resolve("mod_data")
        mgr.teardown_function()
        v2 = mgr.resolve("mod_data")
        assert v1 == v2 == 1

    def test_resolve_nonexistent_fixture(self):
        mgr = FixtureManager()
        try:
            mgr.resolve("nonexistent")
            assert False, "should have raised"
        except LookupError as e:
            assert "nonexistent" in str(e)

    def test_autouse_fixtures(self):
        state = {"setup_done": False}

        @fixture(autouse=True)
        def auto_setup():
            state["setup_done"] = True
            return None

        mgr = FixtureManager()
        mgr.register(auto_setup._fixture_definition)

        def dummy_test():
            pass

        mgr.resolve_test_args(dummy_test)
        assert state["setup_done"] is True

    def test_resolve_test_args(self):
        @fixture
        def value_a():
            return 10

        @fixture
        def value_b():
            return 20

        mgr = FixtureManager()
        mgr.register(value_a._fixture_definition)
        mgr.register(value_b._fixture_definition)

        def test_func(value_a, value_b):
            pass

        kwargs = mgr.resolve_test_args(test_func)
        assert kwargs == {"value_a": 10, "value_b": 20}


class TestRunnerFixtureIntegration:

    def _make_session(self, tmpdir, code):
        tf = Path(tmpdir) / "test_with_fixtures.py"
        tf.write_text(textwrap.dedent(code))
        return Session(paths=[tmpdir])

    def test_simple_fixture_injection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.fixtures import fixture

                @fixture
                def sample_list():
                    return [1, 2, 3]

                def test_uses_fixture(sample_list):
                    assert len(sample_list) == 3
                    assert sum(sample_list) == 6
            """)
            session.run_all()
            code = session.summary()
            assert session.results[0].outcome == Outcome.PASSED
            assert code == 0

    def test_generator_fixture_teardown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.fixtures import fixture

                cleanup_log = []

                @fixture
                def resource():
                    cleanup_log.append("setup")
                    yield {"data": 42}
                    cleanup_log.append("teardown")

                def test_uses_resource(resource):
                    assert resource["data"] == 42
            """)
            session.run_all()
            code = session.summary()
            assert session.results[0].outcome == Outcome.PASSED

    def test_fixture_dependencies_in_runner(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.fixtures import fixture

                @fixture
                def base():
                    return 5

                @fixture
                def doubled(base):
                    return base * 2

                def test_doubled(doubled):
                    assert doubled == 10
            """)
            session.run_all()
            assert session.results[0].outcome == Outcome.PASSED

    def test_autouse_in_runner(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.fixtures import fixture

                state = {"initialized": False}

                @fixture(autouse=True)
                def auto_init():
                    state["initialized"] = True

                def test_auto_init_ran():
                    assert state["initialized"] is True
            """)
            session.run_all()
            assert session.results[0].outcome == Outcome.PASSED

    def test_module_scope_shared(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._make_session(tmpdir, """\
                from pyrunner.fixtures import fixture

                creation_count = []

                @fixture(scope="module")
                def mod_resource():
                    creation_count.append(1)
                    return len(creation_count)

                def test_first(mod_resource):
                    assert mod_resource == 1

                def test_second(mod_resource):
                    assert mod_resource == 1
            """)
            session.run_all()
            code = session.summary()
            assert all(r.outcome == Outcome.PASSED for r in session.results)
            assert code == 0
