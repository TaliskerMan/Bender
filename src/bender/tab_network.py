# Bender — Network Monitor Tab
# Active connections, port checker, DNS lookup, whois, DNS flush, connection counts.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner


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
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(inner)
        self.append(scroll)

        # ── Active Connections ────────────────────────────────────────────────
        conn_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        conn_lbl = Gtk.Label(label="🌐  Active Connections", xalign=0, hexpand=True)
        conn_lbl.add_css_class("heading")
        conn_hdr.append(conn_lbl)

        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", self._refresh_conns)
        conn_hdr.append(refresh_btn)
        inner.append(conn_hdr)

        self._conn_sw, self._conn_buf = _output_view()
        inner.append(self._conn_sw)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=8))

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

        # Initial load
        self._refresh_conns()

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _refresh_conns(self, *_):
        self._conn_buf.set_text("Loading…")
        CommandRunner.run_shell(
            "ss -tunap 2>/dev/null || netstat -tunap 2>/dev/null",
            lambda o, e, r: self._conn_buf.set_text(o or e or "No data")
        )

    def _check_port(self, _btn):
        port = self._port_entry.get_text().strip()
        if not port.isdigit():
            self._port_buf.set_text("Please enter a valid port number.")
            return
        self._port_buf.set_text(f"Checking port {port}…")
        CommandRunner.run_shell(
            f"lsof -iTCP:{port} -sTCP:LISTEN -n -P 2>/dev/null || echo 'No process listening on port {port}'",
            lambda o, e, r: self._port_buf.set_text(o or e or "No data")
        )

    def _do_dig(self, _btn):
        domain = self._dns_entry.get_text().strip()
        if not domain:
            self._dns_buf.set_text("Enter a domain name first.")
            return
        self._dns_buf.set_text(f"Looking up {domain}…")
        CommandRunner.run_shell(
            f"dig {domain}",
            lambda o, e, r: self._dns_buf.set_text(o or e or "dig not found")
        )

    def _do_whois(self, _btn):
        domain = self._whois_entry.get_text().strip()
        if not domain:
            self._whois_buf.set_text("Enter a domain name first.")
            return
        self._whois_buf.set_text(f"Running whois on {domain}…")
        CommandRunner.run_shell(
            f"whois {domain} 2>&1 | head -60",
            lambda o, e, r: self._whois_buf.set_text(o or e or "whois not found")
        )

    def _flush_dns(self, _btn):
        self._flush_buf.set_text("Flushing DNS cache (requires polkit auth)…")
        CommandRunner.run_shell(
            "resolvectl flush-caches && echo 'DNS cache flushed successfully.'",
            lambda o, e, r: self._flush_buf.set_text(o or e or "Failed"),
            use_sudo=True
        )

    def _scan_ddos(self, _btn):
        self._ddos_buf.set_text("Scanning…")
        CommandRunner.run_shell(
            "ss -ntu 2>/dev/null | awk 'NR>1{print $6}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -30",
            lambda o, e, r: self._ddos_buf.set_text(o or "No active connections" if not e else e)
        )
