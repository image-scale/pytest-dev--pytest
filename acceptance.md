# Acceptance Criteria

## Task 1: Core test runner with discovery, execution, reporting, and CLI entry point

### Acceptance Criteria
- [x] Discovers test files matching `test_*.py` pattern in a given directory
- [x] Discovers test functions matching `test_*` pattern within test files
- [x] Executes each discovered test function and catches exceptions
- [x] Tracks results: counts of passed, failed, and error tests
- [x] Reports per-test status: "PASSED" or "FAILED" with the test name
- [x] Prints a summary line like "X passed, Y failed" at the end
- [x] Returns exit code 0 when all tests pass, 1 when any test fails
- [x] Provides a `main()` function that can be called to run the test suite
- [x] Handles test functions that raise AssertionError as "FAILED"
- [x] Handles test functions that raise other exceptions as "ERROR"
- [x] Discovers tests recursively in subdirectories
- [x] Supports running tests from a specific file path passed as argument

## Task 2: Enhanced assertion failure messages

### Acceptance Criteria
- [x] When `assert a == b` fails, the failure message shows the actual values of a and b
- [x] When `assert a != b` fails, the message shows the equal values
- [x] When `assert a > b` fails, the message shows the actual values
- [x] When `assert a in b` fails, the message shows the item and the container
- [x] When `assert a is b` fails, the message shows the object representations
- [x] Supports `assert not expr` showing what the expression evaluated to
- [x] Works with `assert func_call() == expected` showing the function return value
- [x] Provides a function that takes two values and an operator, and formats a detailed comparison message
- [x] Handles string comparisons by showing a diff-like representation for long strings
- [x] The assertion introspection integrates with the test runner to show enhanced messages on failure

## Task 3: Test outcome control with skip, skipif, xfail, and fail

### Acceptance Criteria
- [ ] skip(reason) raises an exception that causes the test to be reported as skipped (not failed)
- [ ] fail(reason) raises an exception that causes the test to fail with the given reason
- [ ] xfail(reason) marks the test as expected to fail; if it does fail it's reported as xfail (expected), not as failure
- [ ] skip_if(condition, reason) conditionally skips a test based on a boolean condition
- [ ] Skipped tests are counted separately in the summary (not as passed or failed)
- [ ] xfail tests that pass unexpectedly are reported as xpass
- [ ] The runner integrates these outcomes into its summary report
- [ ] importorskip(modname) imports a module or skips the test if it can't be imported
- [ ] importorskip with minversion skips if the module version is too low
