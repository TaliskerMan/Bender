# Bender — Command Runner
# Runs shell commands in background threads and delivers results to GTK safely.
#
# SECURITY NOTE (B-03):
# run_shell() with use_sudo=True previously wrapped string commands in
# `pkexec bash -c <string>`, creating a shell injection surface at escalated
# privilege. This has been hardened: privileged commands MUST use the list-form
# run() method directly. run_shell() with use_sudo=True is now rejected.

import threading
import subprocess
from gi.repository import GLib


class CommandRunner:
    """
    Run a shell command in a daemon thread.
    When done, fires callback(stdout, stderr, returncode) on the GLib main loop.

    Security rules:
      - Privileged commands (use_sudo=True) MUST be passed as a list to run().
      - run_shell() is for read-only, non-privileged, hardcoded shell pipelines only.
      - Never pass user-supplied input into run_shell(); use run() with a list instead.
    """

    @staticmethod
    def run(cmd: list, callback, use_sudo: bool = False):
        """
        Execute a command given as an explicit argument list.

        Args:
            cmd:      Command as a list of strings. Strings are NEVER interpreted
                      by a shell, so no injection is possible.
            callback: callable(stdout: str, stderr: str, returncode: int)
            use_sudo: If True, prepends /usr/bin/pkexec to the list for
                      polkit-based privilege escalation. cmd MUST be a list.
        """
        if not isinstance(cmd, list):
            raise TypeError(
                "CommandRunner.run() requires cmd as a list, not a string. "
                "Use run_shell() only for hardcoded, non-privileged pipelines."
            )

        if use_sudo:
            cmd = ['/usr/bin/pkexec'] + cmd

        def _worker():
            try:
                result = subprocess.run(  # nosec B603 — list-form, no shell
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                stdout = ""
                stderr = "Command timed out after 60 seconds."
                returncode = -1
            except FileNotFoundError as e:
                stdout = ""
                stderr = f"Command not found: {e}"
                returncode = 127
            except Exception as e:
                stdout = ""
                stderr = f"Unexpected error: {e}"
                returncode = -1

            GLib.idle_add(callback, stdout, stderr, returncode)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    @staticmethod
    def run_shell(cmd_str: str, callback, use_sudo: bool = False):
        """
        Convenience wrapper for hardcoded shell pipeline strings.

        SECURITY CONSTRAINT: use_sudo=True is NOT permitted here. Passing a
        shell string to pkexec bash -c is a privilege-escalation injection
        surface. Privileged commands must use run() with an explicit list.

        Args:
            cmd_str:  A hardcoded shell pipeline string. NEVER interpolate
                      user input into this string.
            callback: callable(stdout: str, stderr: str, returncode: int)
            use_sudo: Must be False. Raises ValueError if True.
        """
        if use_sudo:
            raise ValueError(
                "run_shell() does not support use_sudo=True. "
                "Use CommandRunner.run(list_of_args, use_sudo=True) instead."
            )
        cmd_list = ["/bin/bash", "-c", cmd_str]
        CommandRunner.run(cmd_list, callback, use_sudo=False)

    @staticmethod
    def command_exists(name: str) -> bool:
        """Check if a command is available on PATH."""
        import shutil
        return shutil.which(name) is not None
