"""Test execution and reporting."""

import inspect
import sys
import time
import traceback
from pathlib import Path

from pyrunner.discovery import discover_test_files, discover_tests
from pyrunner.assertion import introspect_assertion
from pyrunner.outcomes import Skipped, Failed, ExpectedFailure
from pyrunner.fixtures import FixtureManager, Scope
from pyrunner.capture import capsys
from pyrunner.tmpdir import tmp_path, tmp_path_factory


class Outcome:
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"
    XPASS = "XPASS"


class RunResult:
    def __init__(self, filepath, name, outcome, duration=0.0, exception=None):
        self.filepath = filepath
        self.name = name
        self.outcome = outcome
        self.duration = duration
        self.exception = exception

    @property
    def node_id(self):
        if self.name:
            return f"{self.filepath}::{self.name}"
        return self.filepath


class Session:
    """Collects and runs tests, tracking results."""

    def __init__(self, paths=None, verbosity=1):
        self.paths = paths or ["."]
        self.verbosity = verbosity
        self.results = []
        self.fixture_manager = FixtureManager()
        self._register_builtin_fixtures()

    def _register_builtin_fixtures(self):
        for fn in [capsys, tmp_path, tmp_path_factory]:
            if hasattr(fn, '_fixture_definition'):
                self.fixture_manager.register(fn._fixture_definition)

    def collect(self):
        """Discover all test files and test items."""
        all_files = []
        for p in self.paths:
            all_files.extend(discover_test_files(p))
        self.test_items = discover_tests(all_files)
        self._collect_fixtures()
        return self.test_items

    def _collect_fixtures(self):
        """Scan discovered modules for fixture definitions."""
        seen_modules = set()
        for filepath, name, func_or_exc in self.test_items:
            if not callable(func_or_exc):
                continue
            mod = inspect.getmodule(func_or_exc)
            if mod is None or id(mod) in seen_modules:
                continue
            seen_modules.add(id(mod))
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if callable(obj) and hasattr(obj, '_fixture_definition'):
                    self.fixture_manager.register(obj._fixture_definition)

    def run_single_test(self, filepath, name, func_or_exc):
        """Run one test function and record its result."""
        if not callable(func_or_exc):
            result = RunResult(
                filepath, name or "<module>",
                Outcome.ERROR, exception=func_or_exc
            )
            self.results.append(result)
            return result

        xfail_expected = getattr(func_or_exc, '_xfail', False)
        xfail_reason = getattr(func_or_exc, '_xfail_reason', '')

        start = time.perf_counter()
        try:
            kwargs = self.fixture_manager.resolve_test_args(func_or_exc)
            func_or_exc(**kwargs)
            elapsed = time.perf_counter() - start
            if xfail_expected:
                result = RunResult(filepath, name, Outcome.XPASS, duration=elapsed)
            else:
                result = RunResult(filepath, name, Outcome.PASSED, duration=elapsed)
        except Skipped as exc:
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.SKIPPED,
                                duration=elapsed, exception=exc)
        except ExpectedFailure as exc:
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.XFAIL,
                                duration=elapsed, exception=exc)
        except Failed as exc:
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.FAILED,
                                duration=elapsed, exception=exc)
        except AssertionError as exc:
            elapsed = time.perf_counter() - start
            if xfail_expected:
                result = RunResult(filepath, name, Outcome.XFAIL,
                                    duration=elapsed, exception=exc)
            else:
                enhanced = self._enhance_assertion(exc)
                result = RunResult(filepath, name, Outcome.FAILED,
                                    duration=elapsed, exception=enhanced or exc)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            if xfail_expected:
                result = RunResult(filepath, name, Outcome.XFAIL,
                                    duration=elapsed, exception=exc)
            else:
                result = RunResult(filepath, name, Outcome.ERROR,
                                    duration=elapsed, exception=exc)

        self.fixture_manager.teardown_function()
        self.results.append(result)
        return result

    def _enhance_assertion(self, exc):
        """Try to produce an enhanced assertion error with value details."""
        tb = exc.__traceback__
        if tb is None:
            return None
        while tb.tb_next:
            tb = tb.tb_next
        msg = introspect_assertion(tb)
        if msg:
            enhanced = AssertionError(msg)
            enhanced.__traceback__ = exc.__traceback__
            return enhanced
        return None

    def run_all(self):
        """Run all collected tests."""
        self.collect()
        current_file = None
        for filepath, name, func_or_exc in self.test_items:
            if filepath != current_file:
                if current_file is not None:
                    self.fixture_manager.teardown_module()
                current_file = filepath
            result = self.run_single_test(filepath, name, func_or_exc)
            self._report_result(result)
        if current_file is not None:
            self.fixture_manager.teardown_module()
        self.fixture_manager.teardown_session()

    def _report_result(self, result):
        """Print a single test result line."""
        status = result.outcome
        print(f"{result.node_id} {status}")

        if result.exception and result.outcome in (Outcome.FAILED, Outcome.ERROR):
            exc = result.exception
            print(f"    {type(exc).__name__}: {exc}")

    def summary(self):
        """Print summary and return exit code."""
        passed = sum(1 for r in self.results if r.outcome == Outcome.PASSED)
        failed = sum(1 for r in self.results if r.outcome == Outcome.FAILED)
        errors = sum(1 for r in self.results if r.outcome == Outcome.ERROR)
        skipped = sum(1 for r in self.results if r.outcome == Outcome.SKIPPED)
        xfailed = sum(1 for r in self.results if r.outcome == Outcome.XFAIL)
        xpassed = sum(1 for r in self.results if r.outcome == Outcome.XPASS)
        total_time = sum(r.duration for r in self.results)

        parts = []
        if passed:
            parts.append(f"{passed} passed")
        if failed:
            parts.append(f"{failed} failed")
        if errors:
            parts.append(f"{errors} error")
        if skipped:
            parts.append(f"{skipped} skipped")
        if xfailed:
            parts.append(f"{xfailed} xfailed")
        if xpassed:
            parts.append(f"{xpassed} xpassed")
        if not parts:
            parts.append("no tests ran")

        summary_line = ", ".join(parts)
        print(f"\n{'=' * 50}")
        print(f"{summary_line} in {total_time:.2f}s")

        if failed or errors:
            return 1
        return 0


def run_tests(paths=None, verbosity=1):
    """Run tests and return exit code."""
    session = Session(paths=paths, verbosity=verbosity)
    session.run_all()
    return session.summary()


def main(args=None):
    """CLI entry point for the test runner."""
    if args is None:
        args = sys.argv[1:]

    paths = args if args else ["."]
    exit_code = run_tests(paths=paths)
    sys.exit(exit_code)
