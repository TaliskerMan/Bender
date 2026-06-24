# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender. Released under the GNU GPL v3.

"""Enforces the load-bearing security invariants via static (AST) analysis, so a
regression fails the build instead of shipping:

  1. No `run_shell(...)` call passes `use_sudo=True` (privileged commands MUST
     use the list-form `run()`), which is exactly the bug that left four buttons
     throwing ValueError.
  2. No `run_shell(...)` first argument is dynamically built (f-string, `+`
     concatenation, or `.format()`) — that would reintroduce shell injection.
"""

import ast
import glob
import os

_SRC = os.path.join(os.path.dirname(__file__), "..", "src", "bender")


def _callee_name(func):
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _iter_run_shell_calls():
    for path in glob.glob(os.path.join(_SRC, "*.py")):
        tree = ast.parse(open(path).read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _callee_name(node.func) == "run_shell":
                yield path, node


def test_no_run_shell_uses_sudo():
    offenders = []
    for path, node in _iter_run_shell_calls():
        for kw in node.keywords:
            if (
                kw.arg == "use_sudo"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
            ):
                offenders.append(f"{os.path.basename(path)}:{node.lineno}")
    assert not offenders, (
        "run_shell() must never be called with use_sudo=True (it raises "
        "ValueError and the button is dead) — use CommandRunner.run([...], "
        f"use_sudo=True). Offenders: {offenders}"
    )


def test_run_shell_first_arg_is_not_dynamically_built():
    offenders = []
    for path, node in _iter_run_shell_calls():
        if not node.args:
            continue
        arg0 = node.args[0]
        if isinstance(arg0, ast.JoinedStr):
            offenders.append(f"{os.path.basename(path)}:{node.lineno} (f-string)")
        elif isinstance(arg0, ast.BinOp):
            offenders.append(f"{os.path.basename(path)}:{node.lineno} (concatenation)")
        elif isinstance(arg0, ast.Call) and _callee_name(arg0.func) == "format":
            offenders.append(f"{os.path.basename(path)}:{node.lineno} (.format())")
    assert not offenders, (
        "run_shell()'s command string must be a static literal — never an "
        f"f-string/concatenation/.format(). Offenders: {offenders}"
    )


def test_found_some_run_shell_calls():
    # Guard against the matcher silently matching nothing.
    assert any(True for _ in _iter_run_shell_calls())
