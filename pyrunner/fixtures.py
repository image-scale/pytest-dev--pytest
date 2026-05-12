"""Fixture system - dependency injection for test setup and teardown."""

import inspect
from enum import Enum


class Scope(Enum):
    FUNCTION = "function"
    MODULE = "module"
    SESSION = "session"


class FixtureDefinition:
    """Holds metadata about a registered fixture."""

    def __init__(self, func, scope=Scope.FUNCTION, autouse=False, name=None):
        self.func = func
        self.scope = scope
        self.autouse = autouse
        self.name = name or func.__name__
        self.is_generator = inspect.isgeneratorfunction(func)


def fixture(func=None, *, scope="function", autouse=False, name=None):
    """Decorator to mark a function as a fixture provider.

    Can be used with or without arguments:
        @fixture
        def my_fixture(): ...

        @fixture(scope="module")
        def my_fixture(): ...
    """
    scope_enum = Scope(scope) if isinstance(scope, str) else scope

    def decorator(fn):
        defn = FixtureDefinition(fn, scope=scope_enum, autouse=autouse, name=name)
        fn._fixture_definition = defn
        return fn

    if func is not None:
        return decorator(func)
    return decorator


class FixtureManager:
    """Manages fixture resolution, caching, and teardown."""

    def __init__(self):
        self._registry = {}
        self._cache = {}
        self._teardowns = []
        self._scope_cache = {
            Scope.SESSION: {},
            Scope.MODULE: {},
            Scope.FUNCTION: {},
        }
        self._scope_teardowns = {
            Scope.SESSION: [],
            Scope.MODULE: [],
            Scope.FUNCTION: [],
        }

    def register(self, fixture_def):
        """Register a fixture definition."""
        self._registry[fixture_def.name] = fixture_def

    def has_fixture(self, name):
        return name in self._registry

    def get_autouse_fixtures(self):
        """Return names of all autouse fixtures."""
        return [name for name, defn in self._registry.items() if defn.autouse]

    def resolve(self, name):
        """Resolve a fixture by name, using cache and handling dependencies."""
        if name not in self._registry:
            raise LookupError(f"Fixture {name!r} not found")

        defn = self._registry[name]

        if name in self._scope_cache[defn.scope]:
            return self._scope_cache[defn.scope][name]

        deps = self._resolve_dependencies(defn)

        if defn.is_generator:
            gen = defn.func(**deps)
            value = next(gen)
            self._scope_teardowns[defn.scope].append(gen)
        else:
            value = defn.func(**deps)

        self._scope_cache[defn.scope][name] = value
        return value

    def _resolve_dependencies(self, fixture_def):
        """Resolve all parameters a fixture function needs."""
        sig = inspect.signature(fixture_def.func)
        kwargs = {}
        for param_name in sig.parameters:
            if param_name in self._registry:
                kwargs[param_name] = self.resolve(param_name)
        return kwargs

    def resolve_test_args(self, func):
        """Resolve all fixture arguments for a test function."""
        sig = inspect.signature(func)
        kwargs = {}
        autouse_names = self.get_autouse_fixtures()

        for au_name in autouse_names:
            self.resolve(au_name)

        for param_name in sig.parameters:
            if self.has_fixture(param_name):
                kwargs[param_name] = self.resolve(param_name)

        return kwargs

    def teardown_scope(self, scope):
        """Run teardowns for all fixtures in the given scope."""
        teardowns = self._scope_teardowns[scope]
        while teardowns:
            gen = teardowns.pop()
            try:
                next(gen)
            except StopIteration:
                pass
        self._scope_cache[scope].clear()

    def teardown_function(self):
        """Teardown function-scope fixtures."""
        self.teardown_scope(Scope.FUNCTION)

    def teardown_module(self):
        """Teardown module-scope fixtures."""
        self.teardown_scope(Scope.MODULE)

    def teardown_session(self):
        """Teardown session-scope fixtures."""
        self.teardown_scope(Scope.SESSION)

    def teardown_all(self):
        """Teardown all scopes."""
        self.teardown_function()
        self.teardown_module()
        self.teardown_session()
