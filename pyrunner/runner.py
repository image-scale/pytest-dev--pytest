"""Test execution and reporting."""

import sys
import time
from pathlib import Path

from pyrunner.discovery import discover_test_files, discover_tests


class Outcome:
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


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

    def collect(self):
        """Discover all test files and test items."""
        all_files = []
        for p in self.paths:
            all_files.extend(discover_test_files(p))
        self.test_items = discover_tests(all_files)
        return self.test_items

    def run_single_test(self, filepath, name, func_or_exc):
        """Run one test function and record its result."""
        if not callable(func_or_exc):
            result = RunResult(
                filepath, name or "<module>",
                Outcome.ERROR, exception=func_or_exc
            )
            self.results.append(result)
            return result

        start = time.perf_counter()
        try:
            func_or_exc()
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.PASSED, duration=elapsed)
        except AssertionError as exc:
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.FAILED,
                                duration=elapsed, exception=exc)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            result = RunResult(filepath, name, Outcome.ERROR,
                                duration=elapsed, exception=exc)

        self.results.append(result)
        return result

    def run_all(self):
        """Run all collected tests."""
        self.collect()
        for filepath, name, func_or_exc in self.test_items:
            result = self.run_single_test(filepath, name, func_or_exc)
            self._report_result(result)

    def _report_result(self, result):
        """Print a single test result line."""
        if result.outcome == Outcome.PASSED:
            status = "PASSED"
        elif result.outcome == Outcome.FAILED:
            status = "FAILED"
        else:
            status = "ERROR"
        print(f"{result.node_id} {status}")

        if result.exception and result.outcome != Outcome.PASSED:
            exc = result.exception
            print(f"    {type(exc).__name__}: {exc}")

    def summary(self):
        """Print summary and return exit code."""
        passed = sum(1 for r in self.results if r.outcome == Outcome.PASSED)
        failed = sum(1 for r in self.results if r.outcome == Outcome.FAILED)
        errors = sum(1 for r in self.results if r.outcome == Outcome.ERROR)
        total_time = sum(r.duration for r in self.results)

        parts = []
        if passed:
            parts.append(f"{passed} passed")
        if failed:
            parts.append(f"{failed} failed")
        if errors:
            parts.append(f"{errors} error")
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
