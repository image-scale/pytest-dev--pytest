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
- [ ] When `assert a == b` fails, the failure message shows the actual values of a and b
- [ ] When `assert a != b` fails, the message shows the equal values
- [ ] When `assert a > b` fails, the message shows the actual values
- [ ] When `assert a in b` fails, the message shows the item and the container
- [ ] When `assert a is b` fails, the message shows the object representations
- [ ] Supports `assert not expr` showing what the expression evaluated to
- [ ] Works with `assert func_call() == expected` showing the function return value
- [ ] Provides a function that takes two values and an operator, and formats a detailed comparison message
- [ ] Handles string comparisons by showing a diff-like representation for long strings
- [ ] The assertion introspection integrates with the test runner to show enhanced messages on failure
