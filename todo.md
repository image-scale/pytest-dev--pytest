# Todo

## Plan
Build a Python testing framework from the ground up. Start with the core test runner (discovery + execution + reporting), then layer on fixture support, assertion introspection, test outcome control, parametrization, and utility features like approx, raises, warns, monkeypatch, capture, and temp directories.

## Tasks
- [x] Task 1: Core test runner with discovery, execution, reporting, and CLI entry point (discover test_*.py files and test_ functions, run them, report pass/fail/error counts, exit with appropriate code)
- [x] Task 2: Enhanced assertion failure messages that show expression values when an assert statement fails
- [x] Task 3: Test outcome control with skip, skipif, xfail, and fail functions plus marker-based equivalents
- [x] Task 4: Fixture system with dependency injection, scopes (function/module/session), setup/teardown via generators, and autouse
- [x] Task 5: Test parametrization to run a single test function with multiple sets of arguments
- [x] Task 6: Approximate floating-point comparison utility for tolerant numeric equality checks
- [>] Task 7: Exception testing context manager that verifies code raises expected exceptions with optional message matching
- [ ] Task 8: Warning testing context managers that verify code emits expected warnings, plus a deprecated_call helper
- [ ] Task 9: Monkeypatch utility for temporarily modifying attributes, dictionary entries, environment variables, and sys.path during tests
- [ ] Task 10: Stdout/stderr capture fixture that lets tests inspect what was printed during execution
- [ ] Task 11: Temporary directory fixtures that provide unique per-test temp paths with automatic cleanup
