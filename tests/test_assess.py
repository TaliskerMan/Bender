# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender. Released under the GNU GPL v3.

"""Security badges: each check judges its own output."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bender import assess  # noqa: E402


def test_uid0_root_only_is_ok():
    out = "--- Users with UID 0 ---\nroot\n\n--- Sudo group members ---\nchuck\n"
    assert assess.uid0(out) == assess.OK


def test_uid0_extra_account_warns():
    out = "--- Users with UID 0 ---\nroot\ntoor\n\n--- Sudo group members ---\n"
    assert assess.uid0(out) == assess.WARN


def test_login_list_in_november_is_not_a_pass():
    # The old badge logic showed ✅ for any output containing "No",
    # which includes every November date in `last`.
    out = "chuck tty2 :0 Mon Nov  2 09:00 still logged in"
    assert assess.information(out) == assess.INFO


def test_world_writable_and_zombies():
    assert assess.any_lines("") == assess.OK
    assert assess.any_lines("/srv/x\n") == assess.WARN
    assert assess.zombies("No zombie processes found.") == assess.OK
    assert assess.zombies("PID:12 PPID:1 USER:root CMD:x") == assess.WARN


def test_unhide_banner_is_not_a_finding():
    banner = ("Unhide 20220611\n[*]Searching for Hidden processes through "
              "comparison of results of system calls\n")
    assert assess.hidden_processes(banner) == assess.OK
    assert assess.hidden_processes(banner + "Found HIDDEN PID: 4242\n") == assess.WARN
