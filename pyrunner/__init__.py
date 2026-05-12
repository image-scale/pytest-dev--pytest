"""pyrunner - A Python testing framework."""

from pyrunner.runner import main, run_tests, Session, Outcome, RunResult
from pyrunner.discovery import discover_tests, discover_test_files
from pyrunner.assertion import format_comparison, format_unary, introspect_assertion
from pyrunner.outcomes import skip, fail, xfail, skip_if, importorskip, Skipped, Failed, ExpectedFailure
from pyrunner.fixtures import fixture, FixtureManager, Scope
from pyrunner.parametrize import parametrize
from pyrunner.approx import approx
from pyrunner.raises import raises
from pyrunner.warn_utils import warns, deprecated_call
from pyrunner.patching import Patcher

__version__ = "0.1.0"
