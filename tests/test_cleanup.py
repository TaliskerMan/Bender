# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender. Released under the GNU GPL v3.

"""The /dev/shm and /tmp clean-up must only ever delete files that are the
user's own, over a day old, and not open in any running program."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bender import cleanup  # noqa: E402

DAY = 24 * 60 * 60


def _make(path, age_seconds):
    with open(path, "w") as fh:
        fh.write("x")
    old = time.time() - age_seconds
    os.utime(path, (old, old))
    return str(path)


def test_only_old_unused_regular_files(tmp_path):
    old = _make(tmp_path / "old", 2 * DAY)
    _make(tmp_path / "new", 60)                       # too recent
    busy = _make(tmp_path / "busy", 2 * DAY)          # open in a program
    os.mkdir(tmp_path / "folder")                     # not a file
    os.symlink(old, tmp_path / "link")                # not a regular file

    found = cleanup.leftover_files(str(tmp_path), in_use={busy})
    assert found == [old]


def test_other_owners_files_are_left_alone(tmp_path):
    _make(tmp_path / "mine", 2 * DAY)
    found = cleanup.leftover_files(str(tmp_path), uid=os.getuid() + 12345, in_use=set())
    assert found == []


def test_patterns_limit_what_is_considered(tmp_path):
    qipc = _make(tmp_path / "qipc_sharedmemory_x", 2 * DAY)
    gdm = _make(tmp_path / "gdm-session", 2 * DAY)
    _make(tmp_path / "important.txt", 2 * DAY)
    found = cleanup.leftover_files(str(tmp_path), cleanup.TMP_PATTERNS, in_use=set())
    assert sorted(found) == sorted([qipc, gdm])


def test_files_in_use_sees_open_and_mapped_files(tmp_path):
    path = _make(tmp_path / "held-open", 2 * DAY)
    with open(path):
        assert path in cleanup.files_in_use()

    import mmap
    mapped = _make(tmp_path / "mapped", 2 * DAY)
    with open(mapped, "r+b") as fh:
        mm = mmap.mmap(fh.fileno(), 0)
    # File descriptor closed, but the mapping still uses the file.
    try:
        assert mapped in cleanup.files_in_use()
    finally:
        mm.close()


def test_clean_end_to_end_keeps_open_file(tmp_path):
    keep = _make(tmp_path / "open", 2 * DAY)
    gone = _make(tmp_path / "stale", 2 * DAY)
    with open(keep):
        report = cleanup.clean(str(tmp_path))
    assert os.path.exists(keep)
    assert not os.path.exists(gone)
    assert "1 file(s) deleted" in report


def test_clean_reports_nothing_to_do(tmp_path):
    _make(tmp_path / "fresh", 10)
    report = cleanup.clean(str(tmp_path))
    assert report.startswith("Nothing to clean")
    assert os.path.exists(tmp_path / "fresh")
