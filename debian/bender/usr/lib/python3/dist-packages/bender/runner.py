# Bender — Command Runner
# Runs shell commands in background threads and delivers results to GTK safely.

import threading
import subprocess
from gi.repository import GLib


class CommandRunner:
    """
    Run a shell command in a daemon thread.
    When done, fires callback(stdout, stderr, returncode) on the GLib main loop.
    """

    @staticmethod
    def run(cmd: list | str, callback, use_sudo: bool = False, shell: bool = False):
        """
        Args:
            cmd: command as list or shell string
            callback: callable(stdout: str, stderr: str, returncode: int)
            use_sudo: if True, wraps cmd in pkexec for privilege escalation
            shell: if True, treat cmd as a shell string
        """
        if use_sudo:
            if isinstance(cmd, list):
                cmd = ['pkexec'] + cmd
            else:
                cmd = f'pkexec bash -c "{cmd}"'
                shell = True

        def _worker():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    shell=shell
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
        """Convenience wrapper for shell string commands."""
        CommandRunner.run(cmd_str, callback, use_sudo=use_sudo, shell=True)

    @staticmethod
    def command_exists(name: str) -> bool:
        """Check if a command is available on PATH."""
        import shutil
        return shutil.which(name) is not None
