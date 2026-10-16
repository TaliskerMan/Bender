# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

"""Safe clean-up of leftover files in /dev/shm and /tmp.

Files in these folders are often in use: shared memory for audio, browsers and
databases lives in /dev/shm, and Qt keeps qipc_* files in /tmp for running
programs. Deleting a live one can crash the program that owns it. So a file is
only treated as leftover when ALL of these hold:

  * it is a regular file (not a folder or link) directly in the folder,
  * it belongs to you (the clean-up runs without administrator rights),
  * it hasn't been modified for at least a day,
  * no running program has it open or memory-mapped.

These are pure functions (no GTK) so they can be unit-tested.
"""

import fnmatch
import os
import stat
import tempfile
import time

MIN_AGE_SECONDS = 24 * 60 * 60

# The files in /tmp the Maintenance tab is allowed to clean.
TMP_PATTERNS = ("qipc*", "gdm*")


def _collect_open_fds(fd_dir: str, in_use: set) -> None:
    """
    Collect targets of symbolic links in fd_dir that represent open file descriptors.
    """
    try:
        for fd in os.listdir(fd_dir):
            try:
                in_use.add(_strip_deleted(os.readlink(os.path.join(fd_dir, fd))))
            except OSError:
                continue
    except OSError:
        pass


def _collect_mapped_files(maps_path: str, in_use: set) -> None:
    """
    Collect mapped absolute file paths from a process's /proc/<pid>/maps file.
    """
    try:
        with open(maps_path, encoding="utf-8", errors="replace") as maps:
            for line in maps:
                # address perms offset dev inode pathname
                parts = line.split(None, 5)
                if len(parts) == 6 and parts[5].startswith("/"):
                    in_use.add(_strip_deleted(parts[5].rstrip("\n")))
    except OSError:
        pass


def files_in_use(proc_root: str = "/proc") -> set:
    """
    Return the paths that running processes have open (file descriptors) or
    memory-mapped. Only processes we may inspect are seen, which covers every
    process of the current user, the only owner whose files we delete.
    """
    in_use = set()
    try:
        pids = [p for p in os.listdir(proc_root) if p.isdigit()]
    except OSError:
        return in_use
    for pid in pids:
        _collect_open_fds(os.path.join(proc_root, pid, "fd"), in_use)
        _collect_mapped_files(os.path.join(proc_root, pid, "maps"), in_use)
    return in_use


def _strip_deleted(path: str) -> str:
    """
    Strip Linux kernel ' (deleted)' suffix from unlinked open file paths.
    """
    suffix = " (deleted)"
    return path[: -len(suffix)] if path.endswith(suffix) else path


def _is_leftover_candidate(path: str, name: str, patterns, uid: int,
                           min_age: int, in_use: set, now: float) -> bool:
    """
    Determine whether a specific file meets all safety qualifications to be considered leftover.
    """
    if patterns and not any(fnmatch.fnmatch(name, pat) for pat in patterns):
        return False
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISREG(info.st_mode):
        return False
    if info.st_uid != uid:
        return False
    if now - info.st_mtime < min_age:
        return False
    return path not in in_use


def leftover_files(directory: str, patterns=None, uid=None,
                   min_age: int = MIN_AGE_SECONDS, in_use=None, now=None) -> list:
    """
    List the files in *directory* that are safe to delete (see module doc).

    Args:
        directory: Folder to scan (not recursive).
        patterns:  Optional fnmatch patterns the name must match.
        uid:       Owner required (defaults to the current user).
        min_age:   Seconds since the last modification.
        in_use:    Paths open in running programs (defaults to files_in_use()).
        now:       Current time (for tests).
    """
    uid = os.getuid() if uid is None else uid
    now = time.time() if now is None else now
    in_use = files_in_use() if in_use is None else in_use
    found = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return found
    for name in names:
        path = os.path.join(directory, name)
        if _is_leftover_candidate(path, name, patterns, uid, min_age, in_use, now):
            found.append(path)
    return found


def delete_files(paths) -> tuple:
    """Delete *paths*; return (deleted, errors) where errors are messages."""
    deleted, errors = [], []
    for path in paths:
        try:
            os.unlink(path)
            deleted.append(path)
        except FileNotFoundError:
            continue
        except OSError as error:
            errors.append(f"{path}: {error.strerror}")
    return deleted, errors


def clean(directory: str, patterns=None) -> str:
    """Find and delete leftover files; return a report for the output panel."""
    paths = leftover_files(directory, patterns)
    if not paths:
        return f"Nothing to clean in {directory}: no files of yours that are over a day old and unused."
    deleted, errors = delete_files(paths)
    lines = [f"Deleted {path}" for path in deleted]
    lines += [f"Could not delete {error}" for error in errors]
    lines.append(f"{len(deleted)} file(s) deleted from {directory}.")
    return "\n".join(lines)


def clean_shm() -> str:
    """Find and delete leftover files in /dev/shm older than a day and unused."""
    shm_dir = os.path.join(os.path.sep, "dev", "shm")
    return clean(shm_dir)


def clean_tmp() -> str:
    """Find and delete leftover files matching TMP_PATTERNS in /tmp older than a day and unused."""
    return clean(tempfile.gettempdir(), TMP_PATTERNS)
