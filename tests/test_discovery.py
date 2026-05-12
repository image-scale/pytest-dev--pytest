"""Tests for the test discovery module."""

import os
import tempfile
import textwrap
from pathlib import Path

from pyrunner.discovery import discover_test_files, discover_tests, _load_module_from_path


class TestDiscoverTestFiles:

    def test_finds_test_files_in_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test_example.py").write_text("def test_one(): pass\n")
            (Path(tmpdir) / "helper.py").write_text("x = 1\n")

            found = discover_test_files(tmpdir)
            names = [f.name for f in found]
            assert "test_example.py" in names
            assert "helper.py" not in names

    def test_finds_test_files_recursively(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "sub"
            subdir.mkdir()
            (subdir / "test_nested.py").write_text("def test_n(): pass\n")
            (Path(tmpdir) / "test_top.py").write_text("def test_t(): pass\n")

            found = discover_test_files(tmpdir)
            names = [f.name for f in found]
            assert "test_top.py" in names
            assert "test_nested.py" in names

    def test_returns_empty_for_no_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "helper.py").write_text("x = 1\n")
            found = discover_test_files(tmpdir)
            assert found == []

    def test_single_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_single.py"
            tf.write_text("def test_a(): pass\n")
            found = discover_test_files(str(tf))
            assert len(found) == 1
            assert found[0].name == "test_single.py"

    def test_non_test_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nf = Path(tmpdir) / "mymodule.py"
            nf.write_text("def foo(): pass\n")
            found = discover_test_files(str(nf))
            assert found == []

    def test_results_are_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test_zebra.py").write_text("")
            (Path(tmpdir) / "test_alpha.py").write_text("")

            found = discover_test_files(tmpdir)
            names = [f.name for f in found]
            assert names == sorted(names)


class TestDiscoverTests:

    def test_discovers_test_functions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_funcs.py"
            tf.write_text(textwrap.dedent("""\
                def test_add():
                    assert 1 + 1 == 2

                def test_sub():
                    assert 3 - 1 == 2

                def helper():
                    return 42
            """))

            items = discover_tests([tf])
            names = [name for _, name, _ in items]
            assert "test_add" in names
            assert "test_sub" in names
            assert "helper" not in names

    def test_callable_functions_returned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_callable.py"
            tf.write_text("def test_ok(): pass\n")

            items = discover_tests([tf])
            assert len(items) == 1
            _, name, func = items[0]
            assert name == "test_ok"
            assert callable(func)

    def test_import_error_captured(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "test_bad.py"
            tf.write_text("import nonexistent_module_xyz_123\n")

            items = discover_tests([tf])
            assert len(items) == 1
            filepath, name, exc = items[0]
            assert name is None
            assert isinstance(exc, Exception)

    def test_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "test_one.py"
            f1.write_text("def test_a(): pass\n")
            f2 = Path(tmpdir) / "test_two.py"
            f2.write_text("def test_b(): pass\ndef test_c(): pass\n")

            items = discover_tests([f1, f2])
            names = [n for _, n, _ in items]
            assert "test_a" in names
            assert "test_b" in names
            assert "test_c" in names


class TestLoadModule:

    def test_loads_valid_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "mymod.py"
            tf.write_text("VALUE = 42\n")
            mod = _load_module_from_path(tf)
            assert mod.VALUE == 42

    def test_module_has_functions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tf = Path(tmpdir) / "funcs.py"
            tf.write_text("def add(a, b): return a + b\n")
            mod = _load_module_from_path(tf)
            assert mod.add(2, 3) == 5
