# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — Maintenance Tab
# System update, Flatpak update, shared-memory and temp clean-up, log clean-up,
# GNOME app-grid reset.
#
# SECURITY NOTE (B-03):
# Privileged actions run a HARDCODED script through pkexec as an argument list;
# no user input reaches a shell. pkexec handles privilege escalation.
#
# Every action asks before it runs: each one changes or deletes something.

import threading

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from .runner import CommandRunner, describe_exit
from . import cleanup


# Package updates run non-interactively and keep the user's own config files
# when a package ships a new version of one (instead of stopping at dpkg's
# question with nobody to answer it). pkexec clears the environment, so the
# settings are made inside the script. APT_CONFIG adds to, not replaces, the
# system's apt configuration, and both apt-get and nala read it.
SYSTEM_UPDATE_SCRIPT = """set -e
export DEBIAN_FRONTEND=noninteractive
conf=$(mktemp)
trap 'rm -f "$conf"' EXIT
printf '%s\\n' 'Dpkg::Options { "--force-confdef"; "--force-confold"; };' > "$conf"
export APT_CONFIG="$conf"
if command -v nala >/dev/null 2>&1; then
    echo 'Updating with nala...'
    nala update
    # --raw-dpkg (newer nala) hands dpkg's output straight through instead of
    # driving it from a terminal that Bender doesn't have.
    if nala upgrade --help 2>/dev/null | grep -q -- --raw-dpkg; then
        nala upgrade -y --raw-dpkg
    else
        nala upgrade -y
    fi
else
    echo 'nala is not installed; updating with apt-get...'
    apt-get update
    apt-get -y upgrade
fi
echo 'System update complete.'
"""

FLATPAK_UPDATE_SCRIPT = (
    "echo 'Updating your Flatpaks...'; "
    "flatpak update --user -y --noninteractive; "
    "if flatpak list --system | grep -q .; then "
    "echo 'Updating system-wide Flatpaks...'; "
    "pkexec flatpak update --system -y --noninteractive; fi; "
    "echo 'Flatpak update complete.'"
)

CLEAN_LOGS_SCRIPT = (
    "find /var/log -name '*.gz' -type f -print -delete && "
    "echo 'Compressed old logs deleted.'"
)

# Each action provides:
#   label    — display name
#   subtitle — one-line description (must say exactly what it does)
#   icon     — symbolic icon name
#   kind     — "privileged" (script run by pkexec bash), "shell" (hardcoded
#              shell string, no privileges) or "python" (a function, no
#              privileges)
#   cmd      — the script/string, or the function for "python"
#   timeout  — seconds, or None for no limit
#   requires — commands that must be installed (any one of them)
#   confirm  — text of the "are you sure" dialog (every action has one)
#   proceed  — label of the confirm button
ACTIONS = [
    {
        "label":    "System Update",
        "subtitle": "Update package lists and upgrade all packages (nala if installed, otherwise apt-get)",
        "icon":     "software-update-available-symbolic",
        "kind":     "privileged",
        "cmd":      SYSTEM_UPDATE_SCRIPT,
        "timeout":  None,
        "requires": ("nala", "apt-get"),
        "confirm":  "Upgrade every package that has an update? This needs your "
                    "administrator password and can take several minutes; "
                    "output appears when it finishes. Where a package brings a "
                    "new version of a config file you have changed, your "
                    "version is kept.",
        "proceed":  "Update",
    },
    {
        "label":    "Flatpak Update",
        "subtitle": "Update your Flatpak apps, then system-wide ones if there are any",
        "icon":     "package-x-generic-symbolic",
        "kind":     "shell",
        "cmd":      FLATPAK_UPDATE_SCRIPT,
        "timeout":  None,
        "requires": ("flatpak",),
        "confirm":  "Update all installed Flatpak apps? System-wide Flatpaks "
                    "need your administrator password. This can take several "
                    "minutes; output appears when it finishes.",
        "proceed":  "Update",
    },
    {
        "label":    "Clean Shared Memory (/dev/shm)",
        "subtitle": "Delete your own files in /dev/shm that are over a day old and not in use",
        "icon":     "edit-clear-symbolic",
        "kind":     "python",
        "cmd":      lambda: cleanup.clean("/dev/shm"),
        "timeout":  None,
        "requires": (),
        "confirm":  "Delete your own files in /dev/shm that haven't changed "
                    "for a day and that no running program has open? Files "
                    "belonging to other users or the system are left alone. "
                    "Deleted files can't be recovered.",
        "proceed":  "Delete",
    },
    {
        "label":    "Clean Rotated Logs (.gz)",
        "subtitle": "Delete compressed old log archives (*.gz) from /var/log",
        "icon":     "user-trash-symbolic",
        "kind":     "privileged",
        "cmd":      CLEAN_LOGS_SCRIPT,
        "timeout":  300,
        "requires": (),
        "confirm":  "Permanently delete every compressed old log (*.gz) under "
                    "/var/log? Current logs are kept, but older ones you might "
                    "need for troubleshooting are lost. This needs your "
                    "administrator password.",
        "proceed":  "Delete",
    },
    {
        "label":    "Clean Temp Files (/tmp)",
        "subtitle": "Delete your own qipc* and gdm* files in /tmp that are over a day old and not in use",
        "icon":     "folder-templates-symbolic",
        "kind":     "python",
        "cmd":      lambda: cleanup.clean("/tmp", cleanup.TMP_PATTERNS),
        "timeout":  None,
        "requires": (),
        "confirm":  "Delete your own qipc* and gdm* files in /tmp that haven't "
                    "changed for a day and that no running program has open?",
        "proceed":  "Delete",
    },
    {
        "label":    "Reset GNOME App Grid",
        "subtitle": "Reset the app-grid layout, then log out to apply it",
        "icon":     "view-grid-symbolic",
        "kind":     "shell",
        "cmd":      "gsettings reset org.gnome.shell app-picker-layout && sleep 1 && gnome-session-quit --no-prompt",
        "timeout":  60,
        "requires": ("gsettings",),
        "confirm":  "This ends your GNOME session immediately to apply the reset. "
                    "Any unsaved work in open applications will be lost. Continue?",
        "proceed":  "Reset and Log Out",
    },
]


def missing_requirement(action: dict):
    """Return a message if none of the action's required commands exist."""
    required = action.get("requires") or ()
    if required and not any(CommandRunner.command_exists(name) for name in required):
        names = " or ".join(required)
        return f"{names} is not installed, so this action can't run."
    return None


def format_result(stdout_text: str, stderr_text: str, return_code: int,
                  privileged: bool = False) -> str:
    """Text for the output panel: the command's output, then how it ended."""
    parts = []
    if stdout_text:
        parts.append(stdout_text)
    if stderr_text and (return_code != 0 or not stdout_text):
        parts.append(stderr_text)
    parts.append(describe_exit(return_code, stderr_text, privileged))
    return "\n".join(parts)


class _ActionRow(Adw.ActionRow):
    """
    A preferences row representing a single system maintenance task.
    Includes a label, description, icon, run button, and loading spinner.
    """
    def __init__(self, action: dict, output_buf):
        """
        Initializes the maintenance row widget.

        Args:
            action (dict): One entry of ACTIONS.
            output_buf (Gtk.TextBuffer): The shared output text buffer.
        """
        super().__init__(
            title=action["label"],
            subtitle=action["subtitle"],
        )
        self.set_icon_name(action["icon"])
        self._action = action
        self._buf = output_buf

        # Run button as suffix
        self._button = Gtk.Button(label="Run", valign=Gtk.Align.CENTER)
        self._button.add_css_class("suggested-action")
        self._button.connect("clicked", self._run)
        self.add_suffix(self._button)

        # Spinner
        self._spinner = Gtk.Spinner(valign=Gtk.Align.CENTER)
        self.add_suffix(self._spinner)

    def _append(self, text: str):
        self._buf.insert(self._buf.get_end_iter(), text)

    def _run(self, _button):
        """
        Asks for confirmation, then runs the task. Every maintenance action
        changes or deletes something, so none runs on a single click.
        """
        missing = missing_requirement(self._action)
        if missing:
            self._append(f"\n--- Action: {self._action['label']} ---\n{missing}\n")
            return

        root = self.get_root()
        dialog = Adw.MessageDialog(
            transient_for=root if isinstance(root, Gtk.Window) else None,
            heading=self._action["label"],
            body=self._action["confirm"],
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("proceed", self._action.get("proceed", "Continue"))
        dialog.set_response_appearance("proceed", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect(
            "response",
            lambda _d, resp: self._execute() if resp == "proceed" else None,
        )
        dialog.present()

    def _execute(self):
        """Runs the maintenance task in a daemon background thread."""
        self._button.set_sensitive(False)
        self._spinner.start()

        action = self._action
        self._append(f"\n--- Action: {action['label']} ---\nRunning...\n")

        kind = action["kind"]
        if kind == "privileged":
            # Hardcoded script only; nothing typed by the user reaches it.
            cmd_list = ['/usr/bin/pkexec', '/bin/bash', '-c', action["cmd"]]
            CommandRunner.run(cmd_list, self._on_done, use_sudo=False,
                              timeout=action["timeout"])
        elif kind == "shell":
            CommandRunner.run_shell(action["cmd"], self._on_done,
                                    timeout=action["timeout"])
        else:
            func = action["cmd"]

            def _worker():
                try:
                    result = (func(), "", 0)
                except Exception as error:  # report, never crash the UI
                    result = ("", f"Unexpected error: {error}", 1)
                GLib.idle_add(self._on_done, *result)

            threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, stdout_text, stderr_text, return_code):
        """
        Callback handler triggered when the task completes. Re-enables the
        run button, stops the spinner, and writes the output and outcome.
        """
        self._button.set_sensitive(True)
        self._spinner.stop()
        privileged = self._action["kind"] == "privileged"
        self._append(format_result(stdout_text, stderr_text, return_code, privileged) + "\n")


class MaintenanceTab(Gtk.Box):
    """
    MaintenanceTab aggregates multiple system update, cache cleaning, Gnome resets,
    and log deletion tasks into a simple, unified preferences panel.
    """
    def __init__(self):
        """
        Initializes the maintenance panel, setting up preferences groups, rows,
        and the global scrollable text terminal output.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(outer)
        self.append(scroll)

        title = Gtk.Label(label="Maintenance", xalign=0)
        title.add_css_class("title-2")
        title.set_margin_bottom(12)
        outer.append(title)

        group = Adw.PreferencesGroup(title="Actions")

        # ── Global Terminal ───────────────────────────────────────────────────
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                               margin_top=16, margin_bottom=8)

        term_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        terminal_label = Gtk.Label(label="Global Output", xalign=0, hexpand=True)
        terminal_label.add_css_class("heading")
        term_header.append(terminal_label)

        clear_btn = Gtk.Button(label="Clear", valign=Gtk.Align.CENTER)
        clear_btn.connect("clicked", self._clear_terminal)
        term_header.append(clear_btn)

        terminal_box.append(term_header)

        self._console_tv = Gtk.TextView(editable=False, cursor_visible=False,
                                        wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._console_tv.add_css_class("monospace")
        self._console_buf = self._console_tv.get_buffer()

        sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=200)
        sw.set_child(self._console_tv)
        terminal_box.append(sw)

        outer.append(group)
        outer.append(terminal_box)

        for action in ACTIONS:
            row = _ActionRow(action, self._console_buf)
            group.add(row)

    def _clear_terminal(self, _button):
        """
        Clears all text content from the global terminal console output.
        """
        self._console_buf.set_text("")
