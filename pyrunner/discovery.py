"""Test discovery - finds test files and test functions."""

import importlib
import importlib.util
import os
import sys
from pathlib import Path


def discover_test_files(start_dir, pattern="test_*.py"):
    """Walk a directory tree and return paths to files matching the test pattern."""
    start = Path(start_dir)
    if start.is_file():
        if start.name.startswith("test_") and start.suffix == ".py":
            return [start]
        return []

    found = []
    for dirpath, dirnames, filenames in os.walk(str(start)):
        dirnames.sort()
        for fname in sorted(filenames):
            if fname.startswith("test_") and fname.endswith(".py"):
                found.append(Path(dirpath) / fname)
    return found


def _load_module_from_path(filepath):
    """Import a Python file as a module and return it."""
    filepath = Path(filepath).resolve()
    module_name = filepath.stem + "_" + str(hash(str(filepath)) % 10**8)

    spec = importlib.util.spec_from_file_location(module_name, str(filepath))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec from {filepath}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_tests(paths):
    """Discover all test functions from a list of file paths.

    Expands parametrized tests into individual test cases.
    Returns a list of (filepath, test_name, callable) tuples.
    """
    from pyrunner.parametrize import expand_parametrized, make_test_id

    collected = []
    for filepath in paths:
        try:
            module = _load_module_from_path(filepath)
        except Exception as exc:
            collected.append((str(filepath), None, exc))
            continue

        for name in sorted(dir(module)):
            if name.startswith("test_"):
                obj = getattr(module, name)
                if callable(obj):
                    expanded = expand_parametrized(obj)
                    for param_id, bound_func in expanded:
                        test_name = make_test_id(name, param_id)
                        collected.append((str(filepath), test_name, bound_func))
    return collected
