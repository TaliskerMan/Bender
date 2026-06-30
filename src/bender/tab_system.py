# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — System Overview Tab
# Shows hostname, disk, memory, uptime, displays, and top processes.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from .runner import CommandRunner


def _section_label(text: str) -> Gtk.Label:
    lbl = Gtk.Label(label=text, xalign=0)
    lbl.add_css_class("heading")
    lbl.set_margin_top(12)
    lbl.set_margin_bottom(4)
    return lbl


def _mono_view(text: str = "") -> tuple:
    """Returns (scrolled_window, text_buffer) for monospace output."""
    tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
    tv.add_css_class("monospace")
    buf = tv.get_buffer()
    buf.set_text(text)
    sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=120)
    sw.set_child(tv)
    return sw, buf


class SystemTab(Gtk.Box):
    """
    SystemTab constructs a comprehensive system overview display, listing hostname details,
    disk storage availability, memory usage, system load/uptime, active display devices,
    and a top process monitor.
    """
    def __init__(self):
        """
        Initializes the system telemetry panel, builds output scrollable text buffers,
        sets up auto-refresh callbacks, and triggers the initial telemetry gathering.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(inner)
        self.append(scroll)

        # ── Refresh button ────────────────────────────────────────────────────
        refresh_btn = Gtk.Button(label="⟳  Refresh All", halign=Gtk.Align.END)
        refresh_btn.add_css_class("suggested-action")
        refresh_btn.connect("clicked", self._refresh_all)
        inner.append(refresh_btn)

        # ── Hostname / System Info ────────────────────────────────────────────
        inner.append(_section_label("🖥  System Info"))
        _, self._sysinfo_buf = _mono_view("Loading…")
        sw1, _ = _mono_view()
        sw1.get_child().get_buffer().set_text("Loading…")
        self._sysinfo_buf = sw1.get_child().get_buffer()
        inner.append(sw1)

        # ── Disk Usage ────────────────────────────────────────────────────────
        inner.append(_section_label("💽  Disk Usage"))
        sw2, self._disk_buf = _mono_view("Loading…")
        inner.append(sw2)

        # ── Memory ───────────────────────────────────────────────────────────
        inner.append(_section_label("🧠  Memory"))
        sw3, self._mem_buf = _mono_view("Loading…")
        sw3.set_min_content_height(60)
        inner.append(sw3)

        # ── Uptime ────────────────────────────────────────────────────────────
        inner.append(_section_label("⏱  Uptime & Load"))
        sw4, self._uptime_buf = _mono_view("Loading…")
        sw4.set_min_content_height(40)
        inner.append(sw4)

        # ── Displays ─────────────────────────────────────────────────────────
        inner.append(_section_label("🖵  Connected Displays"))
        sw5, self._disp_buf = _mono_view("Loading…")
        sw5.set_min_content_height(60)
        inner.append(sw5)

        # ── Top 10 Processes ─────────────────────────────────────────────────
        inner.append(_section_label("📋  Top 10 Processes (by Memory)"))
        sw6, self._proc_buf = _mono_view("Loading…")
        sw6.set_min_content_height=140
        inner.append(sw6)

        # Auto-refresh every 15 seconds
        self._refresh_all()
        GLib.timeout_add_seconds(15, self._auto_refresh)

    # ── Data loaders ──────────────────────────────────────────────────────────

    def _refresh_all(self, *_):
        """
        Launches asynchronous system shell queries to inspect hostnamectl, df, free,
        uptime, xrandr, and ps statistics.
        """
        CommandRunner.run_shell("hostnamectl", self._on_sysinfo)
        CommandRunner.run_shell("df -hlT -x tmpfs -x devtmpfs", self._on_disk)
        CommandRunner.run_shell("free -h --mega", self._on_mem)
        CommandRunner.run_shell("uptime -p && echo && cat /proc/loadavg", self._on_uptime)
        CommandRunner.run_shell(
            "xrandr -q 2>/dev/null | grep ' connected' || echo 'xrandr not available'",
            self._on_displays
        )
        CommandRunner.run_shell(
            "ps -eo %mem,%cpu,comm --sort=-%mem | head -n 11",
            self._on_procs
        )

    def _auto_refresh(self):
        """
        Periodically triggers refresh_all (returns True to preserve GLib timer repetition).
        """
        self._refresh_all()
        return True  # keep repeating

    def _on_sysinfo(self, stdout_text, stderr_text, return_code):
        """
        Updates the hostnamectl system info terminal text buffer.
        """
        self._sysinfo_buf.set_text(stdout_text or stderr_text or "No data")

    def _on_disk(self, stdout_text, stderr_text, return_code):
        """
        Updates the disk usage terminal text buffer.
        """
        self._disk_buf.set_text(stdout_text or stderr_text or "No data")

    def _on_mem(self, stdout_text, stderr_text, return_code):
        """
        Updates the memory usage terminal text buffer.
        """
        self._mem_buf.set_text(stdout_text or stderr_text or "No data")

    def _on_uptime(self, stdout_text, stderr_text, return_code):
        """
        Updates the uptime & system load terminal text buffer.
        """
        self._uptime_buf.set_text(stdout_text or stderr_text or "No data")

    def _on_displays(self, stdout_text, stderr_text, return_code):
        """
        Updates the connected display terminal text buffer.
        """
        self._disp_buf.set_text(stdout_text or stderr_text or "No displays detected")

    def _on_procs(self, stdout_text, stderr_text, return_code):
        """
        Updates the top process list terminal text buffer.
        """
        self._proc_buf.set_text(stdout_text or stderr_text or "No data")
