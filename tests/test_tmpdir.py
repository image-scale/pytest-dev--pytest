"""Tests for temporary directory fixtures."""

import os
from pathlib import Path

from pyrunner.tmpdir import TempPathFactory


class TestTempPathFactory:

    def test_creates_basetemp(self):
        factory = TempPathFactory()
        try:
            base = factory.getbasetemp()
            assert base.is_dir()
            assert "pyrunner-" in base.name
        finally:
            factory.cleanup()

    def test_basetemp_is_stable(self):
        factory = TempPathFactory()
        try:
            base1 = factory.getbasetemp()
            base2 = factory.getbasetemp()
            assert base1 == base2
        finally:
            factory.cleanup()

    def test_mktemp_creates_directory(self):
        factory = TempPathFactory()
        try:
            p = factory.mktemp("mytest")
            assert p.is_dir()
            assert p.parent == factory.getbasetemp()
        finally:
            factory.cleanup()

    def test_mktemp_numbered(self):
        factory = TempPathFactory()
        try:
            p1 = factory.mktemp("test")
            p2 = factory.mktemp("test")
            assert p1 != p2
            assert p1.name == "test0"
            assert p2.name == "test1"
        finally:
            factory.cleanup()

    def test_mktemp_not_numbered(self):
        factory = TempPathFactory()
        try:
            p = factory.mktemp("fixed", numbered=False)
            assert p.name == "fixed"
        finally:
            factory.cleanup()

    def test_cleanup_removes_basetemp(self):
        factory = TempPathFactory()
        base = factory.getbasetemp()
        assert base.is_dir()
        factory.cleanup()
        assert not base.exists()

    def test_cleanup_is_idempotent(self):
        factory = TempPathFactory()
        factory.getbasetemp()
        factory.cleanup()
        factory.cleanup()

    def test_custom_basetemp(self):
        import tempfile
        custom = Path(tempfile.mkdtemp(prefix="custom-pyrunner-"))
        try:
            factory = TempPathFactory(basetemp=custom)
            assert factory.getbasetemp() == custom
            p = factory.mktemp("sub")
            assert p.parent == custom
        finally:
            factory.cleanup()
            if custom.exists():
                import shutil
                shutil.rmtree(custom)

    def test_mktemp_returns_path_object(self):
        factory = TempPathFactory()
        try:
            p = factory.mktemp("test")
            assert isinstance(p, Path)
        finally:
            factory.cleanup()

    def test_files_in_temp_dir(self):
        factory = TempPathFactory()
        try:
            p = factory.mktemp("test")
            f = p / "data.txt"
            f.write_text("hello")
            assert f.read_text() == "hello"
        finally:
            factory.cleanup()

    def test_multiple_dirs_independent(self):
        factory = TempPathFactory()
        try:
            p1 = factory.mktemp("a")
            p2 = factory.mktemp("b")
            (p1 / "file1.txt").write_text("one")
            (p2 / "file2.txt").write_text("two")
            assert not (p1 / "file2.txt").exists()
            assert not (p2 / "file1.txt").exists()
        finally:
            factory.cleanup()

    def test_cleanup_removes_files(self):
        factory = TempPathFactory()
        p = factory.mktemp("test")
        (p / "file.txt").write_text("data")
        factory.cleanup()
        assert not p.exists()
