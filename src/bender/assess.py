# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

"""How each Security check's output is judged (no GTK, so it can be tested).

Each function takes a check's output and returns one of:
  OK    — nothing of concern was found
  WARN  — something worth reviewing was found
  INFO  — the check lists information; there is no pass or fail
"""

OK = "ok"
WARN = "warn"
INFO = "info"


def uid0(output: str) -> str:
    """Warn if any account other than root has user ID 0."""
    section = output.split("--- Sudo group members ---")[0]
    names = [
        line.strip() for line in section.splitlines()
        if line.strip() and not line.startswith("---")
    ]
    return WARN if any(name != "root" for name in names) else OK


def any_lines(output: str) -> str:
    """Warn if the check printed anything (each line is a finding)."""
    return WARN if output.strip() else OK


def zombies(output: str) -> str:
    return WARN if "PID:" in output else OK


def hidden_processes(output: str) -> str:
    """unhide prints 'Found HIDDEN PID' for each hidden process. (Its banner
    also says "Hidden processes", so match the finding line exactly.)"""
    return WARN if "Found HIDDEN PID" in output else OK


def information(_output: str) -> str:
    return INFO


BADGES = {OK: "✅", WARN: "⚠️", INFO: "ℹ️"}
FAILED_BADGE = "❌"
