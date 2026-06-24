# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — Active Connections Tab
# Separate panel for large volumes of system connections.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner

class ActiveConnectionsTab(Gtk.Box):
    """
    ActiveConnectionsTab displays a scrollable terminal view of current 
    system network connections via command line network utilities.
    """
    def __init__(self):
        """
        Initializes the ActiveConnections tab, constructs the textview container,
        and triggers the initial connection scan.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        
        # ── Header ────────────────────────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="🌐  Active Connections", xalign=0, hexpand=True)
        title.add_css_class("title-2")
        hdr.append(title)

        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.add_css_class("suggested-action")
        refresh_btn.connect("clicked", self._refresh)
        hdr.append(refresh_btn)
        
        inner.append(hdr)
        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=8, margin_bottom=8))

        # ── Terminal View ─────────────────────────────────────────────────────
        self._tv = Gtk.TextView(editable=False, cursor_visible=False,
                                wrap_mode=Gtk.WrapMode.NONE, hexpand=True, vexpand=True)
        self._tv.add_css_class("monospace")
        self._buf = self._tv.get_buffer()

        sw = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        sw.set_child(self._tv)
        inner.append(sw)
        
        self.append(inner)

        # Initial load
        self._refresh()

    def _refresh(self, *_):
        """
        Refreshes the connection log by running ss/netstat in the background
        and displaying the stdout in the monospace TextView buffer.
        """
        self._buf.set_text("Scanning system connections...")
        CommandRunner.run_shell(
            "ss -tunap 2>/dev/null || netstat -tunap 2>/dev/null",
            lambda o, e, r: self._buf.set_text(o or e or "No active connections detected.")
        )
