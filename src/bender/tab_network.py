# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — Network Monitor Tab
# Active connections, port checker, DNS lookup, whois, DNS flush, connection counts.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk  # B-06: removed duplicate import
from .runner import CommandRunner
from .validators import is_valid_domain


def _tool_row(label: str, placeholder: str, btn_label: str, on_clicked) -> tuple:
    """Returns (box_widget, entry_widget) for a label+entry+button row."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                  margin_top=4, margin_bottom=4)
    lbl = Gtk.Label(label=label, width_chars=14, xalign=1)
    lbl.add_css_class("dim-label")
    box.append(lbl)

    entry = Gtk.Entry(placeholder_text=placeholder, hexpand=True)
    box.append(entry)

    button = Gtk.Button(label=btn_label)
    button.connect("clicked", on_clicked)
    box.append(button)

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


def describe_port(port: str, stdout: str, stderr: str, return_code: int) -> str:
    """Text for the Port Checker from ss's output."""
    if return_code != 0:
        return stderr or f"Could not check port {port} (exit code {return_code})."
    if not stdout.strip():
        return f"Nothing is listening on TCP port {port}."
    note = ""
    if "users:(" not in stdout:
        note = ("\n\nThe program's name isn't shown because it belongs to "
                "another user (for example a system service).")
    return f"Listening on TCP port {port}:\n{stdout}{note}"


class NetworkTab(Gtk.Box):
    """
    NetworkTab builds a utility dashboard containing port checking, domain 
    dig queries, whois registries, DNS cache flushing, and connection scans.
    """
    def __init__(self):
        """
        Initializes the NetworkTab widget and lays stdout_text the various sub-panels.
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



    def _check_port(self, _button):
        """
        Shows what is listening on a local TCP port, using ss (iproute2).

        ss lists every listening socket whoever owns it, so a port held by a
        system service is reported correctly even without admin rights. Only
        the program NAME is hidden for other users' processes.
        """
        port = self._port_entry.get_text().strip()
        # Strict numeric validation — isdigit() + range check
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            self._port_buf.set_text("Please enter a valid port number (1–65535).")
            return
        self._port_buf.set_text(f"Checking port {port}…")
        # B-01 FIX: list-form — port is never interpreted by a shell
        CommandRunner.run(
            ["ss", "-H", "-l", "-t", "-n", "-p", "sport", "=", f":{port}"],
            lambda stdout, stderr, return_code: self._port_buf.set_text(
                describe_port(port, stdout, stderr, return_code)
            )
        )

    def _do_dig(self, _):
        """
        Runs a standard DNS lookup (dig) for the entered domain.
        Uses regex checks to ensure domain parameters do not contain shell injection syntax.
        """
        domain = self._dns_entry.get_text().strip()
        if not domain:
            self._dns_buf.set_text("Enter a domain name first.")
            return

        if not is_valid_domain(domain):
            self._dns_buf.set_text("Invalid domain format detected.")
            return

        self._dns_buf.set_text(f"Looking up {domain}…")
        # B-01 FIX: list-form — domain is passed as a discrete argument, not shell-interpolated
        CommandRunner.run(
            ["dig", domain],
            lambda stdout, stderr, return_code: self._dns_buf.set_text(stdout or stderr or "dig not found")
        )

    def _do_whois(self, _button):
        """
        Performs a WHOIS registry lookup on the specified domain name.
        Uses regex input validation and truncates output to 60 lines for legibility.
        """
        domain = self._whois_entry.get_text().strip()
        if not domain:
            self._whois_buf.set_text("Enter a domain name first.")
            return

        if not is_valid_domain(domain):
            self._whois_buf.set_text("Invalid domain format detected.")
            return

        self._whois_buf.set_text(f"Running whois on {domain}…")
        # B-01 FIX: list-form — domain passed as discrete argument
        # Note: head -60 piping dropped in favour of truncating in the callback
        CommandRunner.run(
            ["whois", domain],
            lambda stdout, stderr, return_code: self._whois_buf.set_text(
                "\n".join((stdout or stderr or "whois not found").splitlines()[:60])
            )
        )

    def _flush_dns(self, _button):
        """
        Flushes the DNS cache via resolvectl (requires polkit/pkexec authentication).
        """
        self._flush_buf.set_text("Flushing DNS cache (requires polkit auth)…")
        # List form (no shell). The previous "&& echo success" lived in the shell
        # string; with list-form we report success from the callback instead.
        CommandRunner.run(
            ["resolvectl", "flush-caches"],
            lambda stdout, stderr, return_code: self._flush_buf.set_text(
                "DNS cache flushed successfully." if return_code == 0 else (stderr or "Failed")),
            use_sudo=True
        )

    def _scan_ddos(self, _button):
        """
        Runs connection statistics per IP (DDoS Indicator) by grouping active sockets.
        Pipes ss, awk, cut, sort, and uniq on system to print top connection sources.
        """
        self._ddos_buf.set_text("Scanning…")
        CommandRunner.run_shell(
            # Peer address is field 6; strip its port (after the LAST colon, so
            # IPv6 addresses stay whole) and any [ ] around it.
            "ss -Hntu 2>/dev/null | awk '{a=$6; sub(/:[^:]*$/, \"\", a); "
            "gsub(/^\\[|\\]$/, \"\", a); print a}' | sort | uniq -c | sort -rn | head -30",
            lambda stdout, stderr, return_code: self._ddos_buf.set_text(stdout or "No active connections" if not stderr else stderr)
        )
