# Copyright (C) 2026 Chuck Talk <cwtalk1@gmail.com>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU AGPL v3 for details.

# Bender — Network Monitor Tab
# Active connections, port checker, DNS lookup, whois, DNS flush, connection counts.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw  # B-06: removed duplicate import
from .runner import CommandRunner
import shlex
import re


def _tool_row(label: str, placeholder: str, btn_label: str, on_clicked) -> tuple:
    """Returns (box_widget, entry_widget) for a label+entry+button row."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                  margin_top=4, margin_bottom=4)
    lbl = Gtk.Label(label=label, width_chars=14, xalign=1)
    lbl.add_css_class("dim-label")
    box.append(lbl)

    entry = Gtk.Entry(placeholder_text=placeholder, hexpand=True)
    box.append(entry)

    btn = Gtk.Button(label=btn_label)
    btn.connect("clicked", on_clicked)
    box.append(btn)

    return box, entry


def _output_view() -> tuple:
    """Returns (scrolled_window, text_buffer)."""
    tv = Gtk.TextView(editable=False, cursor_visible=False,
                      wrap_mode=Gtk.WrapMode.WORD_CHAR)
    tv.add_css_class("monospace")
    buf = tv.get_buffer()
    sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=140)
    sw.set_child(tv)
    return sw, buf


class NetworkTab(Gtk.Box):
    """
    NetworkTab builds a utility dashboard containing port checking, domain 
    dig queries, whois registries, DNS cache flushing, and connection scans.
    """
    def __init__(self):
        """
        Initializes the NetworkTab widget and lays out the various sub-panels.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(inner)
        self.append(scroll)



        # ── Port Checker ──────────────────────────────────────────────────────
        port_lbl = Gtk.Label(label="🔌  Port Checker", xalign=0)
        port_lbl.add_css_class("heading")
        port_lbl.set_margin_top(8)
        inner.append(port_lbl)

        port_row, self._port_entry = _tool_row(
            "TCP Port:", "e.g. 22", "Check Port", self._check_port)
        inner.append(port_row)

        self._port_sw, self._port_buf = _output_view()
        self._port_sw.set_min_content_height(80)
        inner.append(self._port_sw)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=8))

        # ── DNS Lookup ────────────────────────────────────────────────────────
        dns_lbl = Gtk.Label(label="🔍  DNS Lookup (dig)", xalign=0)
        dns_lbl.add_css_class("heading")
        dns_lbl.set_margin_top(8)
        inner.append(dns_lbl)

        dns_row, self._dns_entry = _tool_row(
            "Domain:", "e.g. google.com", "Dig", self._do_dig)
        inner.append(dns_row)

        self._dns_sw, self._dns_buf = _output_view()
        self._dns_sw.set_min_content_height(80)
        inner.append(self._dns_sw)

        # ── Whois ─────────────────────────────────────────────────────────────
        whois_row, self._whois_entry = _tool_row(
            "Whois:", "e.g. example.com", "Whois", self._do_whois)
        inner.append(whois_row)

        self._whois_sw, self._whois_buf = _output_view()
        self._whois_sw.set_min_content_height(80)
        inner.append(self._whois_sw)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=8))

        # ── DNS Flush ─────────────────────────────────────────────────────────
        flush_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_top=8)
        flush_lbl = Gtk.Label(label="🧹  DNS Cache Flush", xalign=0, hexpand=True)
        flush_lbl.add_css_class("heading")
        flush_hdr.append(flush_lbl)

        flush_btn = Gtk.Button(label="Flush DNS Cache")
        flush_btn.add_css_class("destructive-action")
        flush_btn.connect("clicked", self._flush_dns)
        flush_hdr.append(flush_btn)
        inner.append(flush_hdr)

        self._flush_sw, self._flush_buf = _output_view()
        self._flush_sw.set_min_content_height(60)
        inner.append(self._flush_sw)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=8))

        # ── Connection Count per IP ───────────────────────────────────────────
        ddos_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_top=8)
        ddos_lbl = Gtk.Label(label="🛡  Connections per IP (DDoS Indicator)", xalign=0, hexpand=True)
        ddos_lbl.add_css_class("heading")
        ddos_hdr.append(ddos_lbl)

        ddos_btn = Gtk.Button(label="Scan")
        ddos_btn.connect("clicked", self._scan_ddos)
        ddos_hdr.append(ddos_btn)
        inner.append(ddos_hdr)

        self._ddos_sw, self._ddos_buf = _output_view()
        self._ddos_sw.set_min_content_height(80)
        inner.append(self._ddos_sw)



    # ── Handlers ──────────────────────────────────────────────────────────────



    def _check_port(self, _btn):
        """
        Checks if a TCP port is open locally by running lsof on the system.
        Performs basic numeric validation before running command runner.
        """
        port = self._port_entry.get_text().strip()
        # Strict numeric validation — isdigit() + range check
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            self._port_buf.set_text("Please enter a valid port number (1–65535).")
            return
        self._port_buf.set_text(f"Checking port {port}…")
        # B-01 FIX: list-form — port is never interpreted by a shell
        CommandRunner.run(
            ["lsof", f"-iTCP:{port}", "-sTCP:LISTEN", "-n", "-P"],
            lambda o, e, r: self._port_buf.set_text(
                o or f"No process listening on port {port}" if r != 0 else o or "No data"
            )
        )

    def _do_dig(self, _btn):
        """
        Runs a standard DNS lookup (dig) for the entered domain.
        Uses regex checks to ensure domain parameters do not contain shell injection syntax.
        """
        domain = self._dns_entry.get_text().strip()
        if not domain:
            self._dns_buf.set_text("Enter a domain name first.")
            return

        if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
            self._dns_buf.set_text("Invalid domain format detected.")
            return

        self._dns_buf.set_text(f"Looking up {domain}…")
        # B-01 FIX: list-form — domain is passed as a discrete argument, not shell-interpolated
        CommandRunner.run(
            ["dig", domain],
            lambda o, e, r: self._dns_buf.set_text(o or e or "dig not found")
        )

    def _do_whois(self, _btn):
        """
        Performs a WHOIS registry lookup on the specified domain name.
        Uses regex input validation and truncates output to 60 lines for legibility.
        """
        domain = self._whois_entry.get_text().strip()
        if not domain:
            self._whois_buf.set_text("Enter a domain name first.")
            return

        if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
            self._whois_buf.set_text("Invalid domain format detected.")
            return

        self._whois_buf.set_text(f"Running whois on {domain}…")
        # B-01 FIX: list-form — domain passed as discrete argument
        # Note: head -60 piping dropped in favour of truncating in the callback
        CommandRunner.run(
            ["whois", domain],
            lambda o, e, r: self._whois_buf.set_text(
                "\n".join((o or e or "whois not found").splitlines()[:60])
            )
        )

    def _flush_dns(self, _btn):
        """
        Flushes the DNS cache via resolvectl (requires polkit/pkexec authentication).
        """
        self._flush_buf.set_text("Flushing DNS cache (requires polkit auth)…")
        CommandRunner.run_shell(
            "resolvectl flush-caches && echo 'DNS cache flushed successfully.'",
            lambda o, e, r: self._flush_buf.set_text(o or e or "Failed"),
            use_sudo=True
        )

    def _scan_ddos(self, _btn):
        """
        Runs connection statistics per IP (DDoS Indicator) by grouping active sockets.
        Pipes ss, awk, cut, sort, and uniq on system to print top connection sources.
        """
        self._ddos_buf.set_text("Scanning…")
        CommandRunner.run_shell(
            "ss -ntu 2>/dev/null | awk 'NR>1{print $6}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -30",
            lambda o, e, r: self._ddos_buf.set_text(o or "No active connections" if not e else e)
        )
