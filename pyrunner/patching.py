"""Monkeypatch utility for temporarily modifying attributes, dicts, env vars, and sys.path."""

import os
import sys
from contextlib import contextmanager

_UNSET = object()


class Patcher:
    """Helper for temporarily patching attributes, dict entries, environment variables, and sys.path.

    All modifications are automatically undone when undo() is called.
    """

    def __init__(self):
        self._attr_patches = []
        self._item_patches = []
        self._saved_syspath = None
        self._saved_cwd = None

    @classmethod
    @contextmanager
    def context(cls):
        """Context manager that creates a Patcher and undoes all changes on exit."""
        p = cls()
        try:
            yield p
        finally:
            p.undo()

    def setattr(self, target, name=_UNSET, value=_UNSET, raising=True):
        """Set an attribute on an object, saving the original value for later restoration.

        Can be called as:
            patcher.setattr(obj, "attr_name", new_value)
            patcher.setattr("module.path.attr", new_value)
        """
        if value is _UNSET:
            if not isinstance(target, str):
                raise TypeError(
                    "use setattr(target, name, value) or "
                    "setattr('dotted.path', value)"
                )
            value = name
            target, name = self._resolve_dotted(target, raising)
        else:
            if not isinstance(name, str):
                raise TypeError("attribute name must be a string")

        old = getattr(target, name, _UNSET)
        if raising and old is _UNSET:
            raise AttributeError(f"{target!r} has no attribute {name!r}")

        self._attr_patches.append((target, name, old))
        setattr(target, name, value)

    def delattr(self, target, name=_UNSET, raising=True):
        """Delete an attribute from an object, saving the original for restoration."""
        if name is _UNSET:
            if not isinstance(target, str):
                raise TypeError(
                    "use delattr(target, name) or delattr('dotted.path')"
                )
            target, name = self._resolve_dotted(target, raising)

        if not hasattr(target, name):
            if raising:
                raise AttributeError(name)
            return

        old = getattr(target, name, _UNSET)
        self._attr_patches.append((target, name, old))
        delattr(target, name)

    def setitem(self, mapping, key, value):
        """Set a dictionary entry, saving the original value."""
        old = mapping.get(key, _UNSET)
        self._item_patches.append((mapping, key, old))
        mapping[key] = value

    def delitem(self, mapping, key, raising=True):
        """Delete a dictionary entry, saving the original value."""
        if key not in mapping:
            if raising:
                raise KeyError(key)
            return

        old = mapping.get(key, _UNSET)
        self._item_patches.append((mapping, key, old))
        del mapping[key]

    def setenv(self, name, value, prepend=None):
        """Set an environment variable."""
        if not isinstance(value, str):
            value = str(value)
        if prepend and name in os.environ:
            value = value + prepend + os.environ[name]
        self.setitem(os.environ, name, value)

    def delenv(self, name, raising=True):
        """Delete an environment variable."""
        self.delitem(os.environ, name, raising=raising)

    def syspath_prepend(self, path):
        """Prepend a path to sys.path."""
        if self._saved_syspath is None:
            self._saved_syspath = sys.path[:]
        sys.path.insert(0, str(path))

    def chdir(self, path):
        """Change the current working directory."""
        if self._saved_cwd is None:
            self._saved_cwd = os.getcwd()
        os.chdir(path)

    def undo(self):
        """Undo all patches in reverse order."""
        for target, name, old in reversed(self._attr_patches):
            if old is _UNSET:
                try:
                    delattr(target, name)
                except AttributeError:
                    pass
            else:
                setattr(target, name, old)
        self._attr_patches.clear()

        for mapping, key, old in reversed(self._item_patches):
            if old is _UNSET:
                try:
                    del mapping[key]
                except KeyError:
                    pass
            else:
                mapping[key] = old
        self._item_patches.clear()

        if self._saved_syspath is not None:
            sys.path[:] = self._saved_syspath
            self._saved_syspath = None

        if self._saved_cwd is not None:
            os.chdir(self._saved_cwd)
            self._saved_cwd = None

    def _resolve_dotted(self, path, raising):
        """Resolve a dotted import path into (object, attr_name)."""
        import importlib
        if "." not in path:
            raise TypeError(f"must be absolute import path, not {path!r}")

        module_path, attr = path.rsplit(".", 1)
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            parts = module_path.rsplit(".", 1)
            if len(parts) == 2:
                parent_mod = importlib.import_module(parts[0])
                mod = getattr(parent_mod, parts[1])
            else:
                raise

        if raising and not hasattr(mod, attr):
            raise AttributeError(f"{mod!r} has no attribute {attr!r}")

        return mod, attr
