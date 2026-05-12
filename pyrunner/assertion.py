"""Enhanced assertion failure messages with value introspection."""

import ast
import difflib
import inspect
import textwrap
import reprlib


_repr = reprlib.Repr()
_repr.maxstring = 200
_repr.maxother = 200
safe_repr = _repr.repr


def format_comparison(left, right, op):
    """Format a detailed comparison message for two values and an operator."""
    lines = []
    left_repr = safe_repr(left)
    right_repr = safe_repr(right)

    if op == "==":
        lines.append(f"assert {left_repr} == {right_repr}")
        if isinstance(left, str) and isinstance(right, str):
            diff_lines = _string_diff(left, right)
            if diff_lines:
                lines.extend(diff_lines)
        elif isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            diff_lines = _sequence_diff(left, right)
            if diff_lines:
                lines.extend(diff_lines)
        elif isinstance(left, dict) and isinstance(right, dict):
            diff_lines = _dict_diff(left, right)
            if diff_lines:
                lines.extend(diff_lines)
    elif op == "!=":
        lines.append(f"assert {left_repr} != {right_repr}")
        lines.append(f"  Both sides are equal: {left_repr}")
    elif op == ">":
        lines.append(f"assert {left_repr} > {right_repr}")
        lines.append(f"  {left_repr} is not greater than {right_repr}")
    elif op == ">=":
        lines.append(f"assert {left_repr} >= {right_repr}")
        lines.append(f"  {left_repr} is not greater than or equal to {right_repr}")
    elif op == "<":
        lines.append(f"assert {left_repr} < {right_repr}")
        lines.append(f"  {left_repr} is not less than {right_repr}")
    elif op == "<=":
        lines.append(f"assert {left_repr} <= {right_repr}")
        lines.append(f"  {left_repr} is not less than or equal to {right_repr}")
    elif op == "in":
        lines.append(f"assert {left_repr} in {right_repr}")
        lines.append(f"  {left_repr} not found in {right_repr}")
    elif op == "not in":
        lines.append(f"assert {left_repr} not in {right_repr}")
        lines.append(f"  {left_repr} unexpectedly found in {right_repr}")
    elif op == "is":
        lines.append(f"assert {left_repr} is {right_repr}")
        lines.append(f"  {left_repr} is not {right_repr}")
    elif op == "is not":
        lines.append(f"assert {left_repr} is not {right_repr}")
        lines.append(f"  both reference the same object")
    else:
        lines.append(f"assert {left_repr} {op} {right_repr}")

    return "\n".join(lines)


def format_unary(value, op="not"):
    """Format a failure message for unary assertions."""
    val_repr = safe_repr(value)
    if op == "not":
        return f"assert not {val_repr}\n  value is truthy: {val_repr}"
    return f"assert {op} {val_repr}"


def _string_diff(left, right):
    """Generate a diff-style comparison for strings."""
    if len(left) < 20 and len(right) < 20:
        return []

    left_lines = left.splitlines(keepends=True)
    right_lines = right.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        left_lines, right_lines,
        fromfile="left", tofile="right", lineterm=""
    ))
    if diff:
        return ["  Diff:"] + ["  " + line for line in diff]
    return []


def _sequence_diff(left, right):
    """Generate comparison details for sequences."""
    lines = []
    if len(left) != len(right):
        lines.append(f"  Length mismatch: {len(left)} vs {len(right)}")

    min_len = min(len(left), len(right))
    first_diff = None
    for i in range(min_len):
        if left[i] != right[i]:
            first_diff = i
            break

    if first_diff is not None:
        lines.append(f"  First differing element at index {first_diff}:")
        lines.append(f"    left[{first_diff}]  = {safe_repr(left[first_diff])}")
        lines.append(f"    right[{first_diff}] = {safe_repr(right[first_diff])}")
    elif len(left) != len(right):
        longer = "left" if len(left) > len(right) else "right"
        lines.append(f"  {longer} has {abs(len(left) - len(right))} extra element(s)")

    return lines


def _dict_diff(left, right):
    """Generate comparison details for dicts."""
    lines = []
    left_keys = set(left.keys())
    right_keys = set(right.keys())

    only_left = left_keys - right_keys
    only_right = right_keys - left_keys
    common = left_keys & right_keys

    if only_left:
        lines.append(f"  Keys only in left: {sorted(only_left)}")
    if only_right:
        lines.append(f"  Keys only in right: {sorted(only_right)}")

    differing = []
    for k in sorted(common, key=repr):
        if left[k] != right[k]:
            differing.append(k)

    if differing:
        lines.append("  Differing values:")
        for k in differing[:5]:
            lines.append(f"    key={safe_repr(k)}: {safe_repr(left[k])} vs {safe_repr(right[k])}")
        if len(differing) > 5:
            lines.append(f"    ...and {len(differing) - 5} more")

    return lines


def introspect_assertion(tb):
    """Attempt to extract assertion details from a traceback object.

    Returns an enhanced error message string, or None if introspection fails.
    """
    try:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        with open(filename, "r") as f:
            source_lines = f.readlines()
        if 0 < lineno <= len(source_lines):
            line = source_lines[lineno - 1].strip()
            if line.startswith("assert "):
                expr_text = line[len("assert "):]
                if "," in expr_text:
                    expr_text = expr_text.rsplit(",", 1)[0].strip()
                return _analyze_assert_expression(expr_text, frame)
    except (OSError, TypeError, IOError):
        pass
    return None


def _analyze_assert_expression(expr_text, frame):
    """Parse and analyze an assert expression to produce a rich failure message."""
    try:
        tree = ast.parse(expr_text, mode="eval")
    except SyntaxError:
        return None

    node = tree.body

    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left_val = _eval_node(node.left, frame)
        right_val = _eval_node(node.comparators[0], frame)
        op = _op_to_str(node.ops[0])
        if left_val is not _EVAL_FAILED and right_val is not _EVAL_FAILED:
            return format_comparison(left_val, right_val, op)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        val = _eval_node(node.operand, frame)
        if val is not _EVAL_FAILED:
            return format_unary(val, "not")

    return None


_EVAL_FAILED = object()


def _eval_node(node, frame):
    """Safely evaluate an AST node in the given frame's context."""
    try:
        code = compile(ast.Expression(body=node), "<assertion>", "eval")
        return eval(code, frame.f_globals, frame.f_locals)
    except Exception:
        return _EVAL_FAILED


def _op_to_str(op):
    """Convert an AST comparison operator to its string representation."""
    op_map = {
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
        ast.Is: "is",
        ast.IsNot: "is not",
        ast.In: "in",
        ast.NotIn: "not in",
    }
    return op_map.get(type(op), str(op))
