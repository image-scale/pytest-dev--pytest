"""Test parametrization - run a test with multiple argument sets."""

import itertools


class ParameterSet:
    """A single set of parameter values for a parametrized test."""

    def __init__(self, values, param_id=None):
        if not isinstance(values, (tuple, list)):
            values = (values,)
        else:
            values = tuple(values)
        self.values = values
        self.id = param_id


class ParametrizeInfo:
    """Stores parametrize metadata attached to a test function."""

    def __init__(self, argnames, argvalues):
        if isinstance(argnames, str):
            argnames = [n.strip() for n in argnames.split(",")]
        self.argnames = list(argnames)
        self.param_sets = []
        for val in argvalues:
            if isinstance(val, ParameterSet):
                self.param_sets.append(val)
            elif len(self.argnames) == 1:
                self.param_sets.append(ParameterSet((val,)))
            else:
                self.param_sets.append(ParameterSet(val))


def parametrize(argnames, argvalues):
    """Decorator to parametrize a test function with multiple argument sets.

    Usage:
        @parametrize("x,y,expected", [(1,2,3), (4,5,9)])
        def test_add(x, y, expected):
            assert x + y == expected
    """
    info = ParametrizeInfo(argnames, argvalues)

    def decorator(func):
        if not hasattr(func, '_parametrize_marks'):
            func._parametrize_marks = []
        func._parametrize_marks.append(info)
        return func

    return decorator


def expand_parametrized(func):
    """Expand a parametrized function into multiple concrete test functions.

    Returns a list of (test_id_suffix, callable) pairs.
    """
    marks = getattr(func, '_parametrize_marks', None)
    if not marks:
        return [(None, func)]

    all_combos = _compute_combinations(marks)
    expanded = []
    for combo in all_combos:
        names, values, test_id = combo
        kwargs = dict(zip(names, values))

        def make_bound(kw):
            def bound_test(**extra_kwargs):
                merged = {**kw, **extra_kwargs}
                return func(**merged)
            bound_test.__name__ = func.__name__
            bound_test.__wrapped__ = func
            for attr in ('_fixture_definition', '_xfail', '_xfail_reason'):
                if hasattr(func, attr):
                    setattr(bound_test, attr, getattr(func, attr))
            return bound_test

        expanded.append((test_id, make_bound(kwargs)))

    return expanded


def _compute_combinations(marks):
    """Compute cartesian product of all parametrize marks."""
    per_mark = []
    for mark in marks:
        entries = []
        for ps in mark.param_sets:
            ps_id = ps.id if ps.id else "-".join(str(v) for v in ps.values)
            entries.append((mark.argnames, ps.values, ps_id))
        per_mark.append(entries)

    if len(per_mark) == 1:
        return per_mark[0]

    result = []
    for combo in itertools.product(*per_mark):
        merged_names = []
        merged_values = []
        merged_ids = []
        for names, values, tid in combo:
            merged_names.extend(names)
            merged_values.extend(values)
            merged_ids.append(tid)
        combined_id = "-".join(merged_ids)
        result.append((merged_names, tuple(merged_values), combined_id))

    return result


def make_test_id(base_name, param_id):
    """Create a test ID with parameter info."""
    if param_id is None:
        return base_name
    return f"{base_name}[{param_id}]"
