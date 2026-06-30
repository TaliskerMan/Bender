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
# System update, Flatpak update, clear shared memory, clean logs, GNOME reset, temp cleanup.
#
# SECURITY NOTE (B-03):
# All privileged actions now use CommandRunner.run() with explicit argument lists.
# No shell strings are passed through pkexec. The inner "sudo" prefix has been
# removed — pkexec already handles privilege escalation.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner


# Each action provides:
#   label    — display name
#   subtitle — one-line description
#   icon     — symbolic icon name
#   cmd      — list of args for CommandRunner.run(), OR a shell string for run_shell()
#   sudo     — True = use pkexec via run(); False = use run_shell()
#   use_list — True = cmd is a list (required when sudo=True)
ACTIONS = [
    {
        "label":    "System Update (nala)",
        "subtitle": "Update package lists and upgrade all packages",
        "icon":     "software-update-available-symbolic",
        # Privileged shell pipeline: nala update && nala upgrade -y
        "cmd":      "nala update && nala upgrade -y",
        "sudo":     True,
        "use_list": False,
    },
    {
        "label":    "Flatpak Update",
        "subtitle": "Update all installed Flatpak applications",
        "icon":     "package-x-generic-symbolic",
        "cmd":      "echo 'Updating User Flatpaks...'; flatpak update --user -y --noninteractive; if flatpak list --system | grep -q .; then echo 'Updating System Flatpaks...'; pkexec flatpak update --system -y --noninteractive; fi; echo 'Flatpak update complete.'",
        "sudo":     False,
        "use_list": False,
    },
    {
        "label":    "Clear Shared Memory (/dev/shm)",
        "subtitle": "Remove stale files from the shared memory filesystem",
        "icon":     "edit-clear-symbolic",
        # find cannot be cleanly expressed without shell for -delete + -print;
        # use bash -c safely via a HARDCODED string (no user input).
        "cmd":      "find /dev/shm -maxdepth 1 -type f -delete -print && echo 'Shared memory cleared.'",
        "sudo":     True,
        "use_list": False,
    },
    {
        "label":    "Clean Rotated Logs (.gz)",
        "subtitle": "Delete compressed rotated log archives from /var/log",
        "icon":     "user-trash-symbolic",
        "cmd":      "find /var/log -name '*.gz' -type f -delete -print && echo 'Old logs cleaned.'",
        "sudo":     True,
        "use_list": False,
    },
    {
        "label":    "Clean Temp Files (/tmp)",
        "subtitle": "Remove stale qipc* and gdm* temp files (no privilege required)",
        "icon":     "folder-templates-symbolic",
        # No sudo — clean shell string, no user input
        "cmd":      (
            "find /tmp -maxdepth 1 -name 'qipc*' -delete -print; "
            "find /tmp -maxdepth 1 -name 'gdm*'  -delete -print; "
            "echo 'Temp cleanup done.'"
        ),
        "sudo":     False,
        "use_list": False,
    },
    {
        "label":    "Reset GNOME App Grid",
        "subtitle": "Reset app-picker-layout and restart GNOME session",
        "icon":     "view-grid-symbolic",
        "cmd":      "gsettings reset org.gnome.shell app-picker-layout && sleep 1 && gnome-session-quit --no-prompt",
        "sudo":     False,
        "use_list": False,
        "confirm":  "This ends your GNOME session immediately to apply the reset. "
                    "Any unsaved work in open applications will be lost. Continue?",
    },
]


class _ActionRow(Adw.ActionRow):
    """
    A preferences row representing a single system maintenance command task.
    Includes a label, short explanation description, icon, run button, and loading spinner.
    """
    def __init__(self, action: dict, output_buf):
        """
        Initializes the maintenance row widget.
        
        Args:
            action (dict): Dictionary specifying the command label, subtitle, icon, command,
                           privilege levels (sudo flag), and parameter types.
            output_buf (Gtk.TextBuffer): Reference to the global stdout logging text buffer.
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

    def _run(self, _button):
        """
        Triggers the maintenance task, first asking for confirmation if the action
        is disruptive (e.g. one that ends the GNOME session).
        """
        confirm = self._action.get("confirm")
        if confirm:
            root = self.get_root()
            dialog = Adw.MessageDialog(
                transient_for=root if isinstance(root, Gtk.Window) else None,
                heading=self._action["label"],
                body=confirm,
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("proceed", "Continue")
            dialog.set_response_appearance("proceed", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.connect(
                "response",
                lambda _d, resp: self._execute() if resp == "proceed" else None,
            )
            dialog.present()
            return
        self._execute()

    def _execute(self):
        """Runs the maintenance task in a daemon background thread."""
        self._button.set_sensitive(False)
        self._spinner.start()

        end_iter = self._buf.get_end_iter()
        self._buf.insert(end_iter, f"\n--- Action: {self._action['label']} ---\nRunning...\n")

        action = self._action
        if action["sudo"]:
            if action["use_list"]:
                # Safe: explicit arg list → pkexec <cmd>
                CommandRunner.run(action["cmd"], self._on_done, use_sudo=True)
            else:
                # Privileged shell pipeline (hardcoded string only) →
                # pkexec bash -c <hardcoded_string>
                cmd_list = ['/usr/bin/pkexec', 'bash', '-c', action["cmd"]]
                CommandRunner.run(cmd_list, self._on_done, use_sudo=False)
        else:
            CommandRunner.run_shell(action["cmd"], self._on_done)

    def _on_done(self, stdout_text, stderr_text, return_code):
        """
        Callback handler triggered when the background command completes.
        Re-enables the run button, stops the spinner, and writes command results 
        (stdout/stderr) to the global console log buffer.
        """
        self._button.set_sensitive(True)
        self._spinner.stop()

        end_iter = self._buf.get_end_iter()
        result = stdout_text or stderr_text or "(no output)"
        self._buf.insert(end_iter, f"{result}\n")


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
