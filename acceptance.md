# Acceptance Criteria

## Task 1: Core test runner with discovery, execution, reporting, and CLI entry point

### Acceptance Criteria
- [ ] Discovers test files matching `test_*.py` pattern in a given directory
- [ ] Discovers test functions matching `test_*` pattern within test files
- [ ] Executes each discovered test function and catches exceptions
- [ ] Tracks results: counts of passed, failed, and error tests
- [ ] Reports per-test status: "PASSED" or "FAILED" with the test name
- [ ] Prints a summary line like "X passed, Y failed" at the end
- [ ] Returns exit code 0 when all tests pass, 1 when any test fails
- [ ] Provides a `main()` function that can be called to run the test suite
- [ ] Handles test functions that raise AssertionError as "FAILED"
- [ ] Handles test functions that raise other exceptions as "ERROR"
- [ ] Discovers tests recursively in subdirectories
- [ ] Supports running tests from a specific file path passed as argument
