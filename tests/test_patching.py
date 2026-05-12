"""Tests for the monkeypatch/patching utility."""

import os
import sys
import tempfile
from pathlib import Path

from pyrunner.patching import Patcher


class _SampleModule:
    VALUE = 42
    NAME = "original"


class TestSetattr:

    def test_setattr_on_object(self):
        p = Patcher()
        obj = _SampleModule()
        p.setattr(obj, "VALUE", 99)
        assert obj.VALUE == 99
        p.undo()
        assert obj.VALUE == 42

    def test_setattr_restores_on_undo(self):
        p = Patcher()
        p.setattr(_SampleModule, "VALUE", 100)
        assert _SampleModule.VALUE == 100
        p.undo()
        assert _SampleModule.VALUE == 42

    def test_setattr_dotted_path(self):
        p = Patcher()
        p.setattr("os.sep", "/PATCHED/")
        assert os.sep == "/PATCHED/"
        p.undo()
        assert os.sep != "/PATCHED/"

    def test_setattr_raising_on_missing(self):
        p = Patcher()
        obj = _SampleModule()
        try:
            p.setattr(obj, "NONEXISTENT", 1)
            assert False
        except AttributeError:
            pass
        p.undo()

    def test_setattr_not_raising_on_missing(self):
        p = Patcher()
        obj = _SampleModule()
        p.setattr(obj, "NEW_ATTR", 1, raising=False)
        assert obj.NEW_ATTR == 1
        p.undo()
        assert not hasattr(obj, "NEW_ATTR")


class TestDelattr:

    def test_delattr_and_restore(self):
        p = Patcher()
        obj = _SampleModule()
        obj.TEMP = "temporary"
        p.delattr(obj, "TEMP")
        assert not hasattr(obj, "TEMP")
        p.undo()
        assert obj.TEMP == "temporary"

    def test_delattr_raising_on_missing(self):
        p = Patcher()
        obj = _SampleModule()
        try:
            p.delattr(obj, "NONEXISTENT")
            assert False
        except AttributeError:
            pass
        p.undo()

    def test_delattr_not_raising(self):
        p = Patcher()
        obj = _SampleModule()
        p.delattr(obj, "NONEXISTENT", raising=False)
        p.undo()


class TestSetitem:

    def test_setitem_new_key(self):
        p = Patcher()
        d = {"a": 1}
        p.setitem(d, "b", 2)
        assert d == {"a": 1, "b": 2}
        p.undo()
        assert d == {"a": 1}

    def test_setitem_existing_key(self):
        p = Patcher()
        d = {"a": 1}
        p.setitem(d, "a", 99)
        assert d["a"] == 99
        p.undo()
        assert d["a"] == 1


class TestDelitem:

    def test_delitem_existing(self):
        p = Patcher()
        d = {"a": 1, "b": 2}
        p.delitem(d, "b")
        assert "b" not in d
        p.undo()
        assert d["b"] == 2

    def test_delitem_missing_raises(self):
        p = Patcher()
        d = {"a": 1}
        try:
            p.delitem(d, "x")
            assert False
        except KeyError:
            pass
        p.undo()

    def test_delitem_missing_not_raising(self):
        p = Patcher()
        d = {"a": 1}
        p.delitem(d, "x", raising=False)
        p.undo()


class TestSetenv:

    def test_setenv_new_var(self):
        p = Patcher()
        var = "_PYRUNNER_TEST_VAR_123"
        if var in os.environ:
            del os.environ[var]
        p.setenv(var, "hello")
        assert os.environ[var] == "hello"
        p.undo()
        assert var not in os.environ

    def test_setenv_overwrites(self):
        p = Patcher()
        var = "_PYRUNNER_TEST_VAR_456"
        os.environ[var] = "original"
        p.setenv(var, "patched")
        assert os.environ[var] == "patched"
        p.undo()
        assert os.environ[var] == "original"
        del os.environ[var]

    def test_setenv_prepend(self):
        p = Patcher()
        var = "_PYRUNNER_TEST_VAR_789"
        os.environ[var] = "world"
        p.setenv(var, "hello", prepend=":")
        assert os.environ[var] == "hello:world"
        p.undo()
        assert os.environ[var] == "world"
        del os.environ[var]


class TestDelenv:

    def test_delenv_existing(self):
        p = Patcher()
        var = "_PYRUNNER_TEST_DEL_VAR"
        os.environ[var] = "value"
        p.delenv(var)
        assert var not in os.environ
        p.undo()
        assert os.environ[var] == "value"
        del os.environ[var]

    def test_delenv_missing_raises(self):
        p = Patcher()
        try:
            p.delenv("_PYRUNNER_NONEXISTENT_VAR")
            assert False
        except KeyError:
            pass
        p.undo()


class TestSyspathPrepend:

    def test_syspath_prepend_and_restore(self):
        p = Patcher()
        original = sys.path[:]
        p.syspath_prepend("/fake/path/for/test")
        assert sys.path[0] == "/fake/path/for/test"
        p.undo()
        assert sys.path == original


class TestChdir:

    def test_chdir_and_restore(self):
        p = Patcher()
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            p.chdir(tmpdir)
            assert os.getcwd() == tmpdir
            p.undo()
            assert os.getcwd() == original_cwd


class TestContextManager:

    def test_context_undoes_on_exit(self):
        d = {"key": "original"}
        with Patcher.context() as p:
            p.setitem(d, "key", "patched")
            assert d["key"] == "patched"
        assert d["key"] == "original"

    def test_context_undoes_on_exception(self):
        d = {"key": "original"}
        try:
            with Patcher.context() as p:
                p.setitem(d, "key", "patched")
                raise RuntimeError("oops")
        except RuntimeError:
            pass
        assert d["key"] == "original"


class TestMultiplePatches:

    def test_multiple_attrs_undone_in_order(self):
        p = Patcher()
        obj = _SampleModule()
        p.setattr(obj, "VALUE", 10)
        p.setattr(obj, "VALUE", 20)
        assert obj.VALUE == 20
        p.undo()
        assert obj.VALUE == 42

    def test_undo_is_idempotent(self):
        p = Patcher()
        d = {"a": 1}
        p.setitem(d, "a", 2)
        p.undo()
        p.undo()
        assert d["a"] == 1
