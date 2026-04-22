# Bender — Proxy Manager Tab
# Manages tinyproxy: start/stop, blocklist management, live logs, auto-update.

import threading
import subprocess
import shutil
import shlex
import re

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from .runner import CommandRunner


FILTER_FILE = "/etc/tinyproxy/filter"
LOG_FILE    = "/var/log/tinyproxy/tinyproxy.log"
HOSTS_URL   = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"


class ProxyTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._log_tail_proc = None

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(inner)
        self.append(scroll)

        # ── Check if tinyproxy is installed ───────────────────────────────────
        if not shutil.which("tinyproxy"):
            banner = Adw.StatusPage(
                title="Tinyproxy Not Installed",
                description=(
                    "Install tinyproxy to use the Proxy Manager tab.\n\n"
                    "sudo apt install tinyproxy"
                ),
                icon_name="network-vpn-symbolic",
            )
            self.append(banner)
            return

        # ── Status header ──────────────────────────────────────────────────────
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, margin_bottom=4)
        inner.append(status_box)

        status_title = Gtk.Label(label="Proxy Status", xalign=0, hexpand=True)
        status_title.add_css_class("title-2")
        status_box.append(status_title)

        self._status_badge = Gtk.Label(label="⏳ Checking…")
        status_box.append(self._status_badge)

        refresh_status_btn = Gtk.Button(label="⟳")
        refresh_status_btn.connect("clicked", self._refresh_status)
        status_box.append(refresh_status_btn)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Start / Stop row ──────────────────────────────────────────────────
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_top=4)
        inner.append(ctrl_box)

        start_btn = Gtk.Button(label="▶  Start Proxy")
        start_btn.add_css_class("suggested-action")
        start_btn.connect("clicked", self._start_proxy)
        ctrl_box.append(start_btn)

        stop_btn = Gtk.Button(label="■  Stop Proxy")
        stop_btn.add_css_class("destructive-action")
        stop_btn.connect("clicked", self._stop_proxy)
        ctrl_box.append(stop_btn)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Blocklist editor ──────────────────────────────────────────────────
        bl_lbl = Gtk.Label(label="🚫  Blocklist", xalign=0)
        bl_lbl.add_css_class("heading")
        bl_lbl.set_margin_top(4)
        inner.append(bl_lbl)

        bl_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        inner.append(bl_ctrl)

        self._quick_entry = Gtk.Entry(placeholder_text="domain to block…", hexpand=True)
        bl_ctrl.append(self._quick_entry)

        quick_add_btn = Gtk.Button(label="Quick Add")
        quick_add_btn.connect("clicked", self._quick_add)
        bl_ctrl.append(quick_add_btn)

        update_btn = Gtk.Button(label="Auto-Update (Steven Black)")
        update_btn.connect("clicked", self._auto_update)
        bl_ctrl.append(update_btn)

        load_bl_btn = Gtk.Button(label="Load Blocklist")
        load_bl_btn.connect("clicked", self._load_blocklist)
        bl_ctrl.append(load_bl_btn)

        save_bl_btn = Gtk.Button(label="Save Blocklist")
        save_bl_btn.add_css_class("suggested-action")
        save_bl_btn.connect("clicked", self._save_blocklist)
        bl_ctrl.append(save_bl_btn)

        self._bl_tv = Gtk.TextView(wrap_mode=Gtk.WrapMode.NONE)
        self._bl_tv.add_css_class("monospace")
        self._bl_buf = self._bl_tv.get_buffer()
        bl_sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=180)
        bl_sw.set_child(self._bl_tv)
        inner.append(bl_sw)

        inner.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Live log tail ─────────────────────────────────────────────────────
        log_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_top=4)
        inner.append(log_hdr)

        log_lbl = Gtk.Label(label="📋  Live Proxy Log", xalign=0, hexpand=True)
        log_lbl.add_css_class("heading")
        log_hdr.append(log_lbl)

        self._log_tv = Gtk.TextView(editable=False, cursor_visible=False,
                                   wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._log_tv.add_css_class("monospace")
        self._log_buf = self._log_tv.get_buffer()
        log_sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=120)
        log_sw.set_child(self._log_tv)
        inner.append(log_sw)

        tail_btn = Gtk.Button(label="▶  Tail Log (last 50 lines)")
        tail_btn.connect("clicked", self._tail_log)
        log_hdr.append(tail_btn)

        # ── Action status area ────────────────────────────────────────────────
        self._action_status = Gtk.Label(label="", xalign=0)
        self._action_status.add_css_class("dim-label")
        inner.append(self._action_status)

        self._refresh_status()
        self._load_blocklist()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_status(self, *_):
        self._status_badge.set_text("⏳ Checking…")
        CommandRunner.run_shell(
            "systemctl is-active tinyproxy",
            self._on_status
        )

    def _on_status(self, out, err, rc):
        if out.strip() == "active":
            self._status_badge.set_text("🟢  Active")
        else:
            self._status_badge.set_text("🔴  Inactive")

    def _start_proxy(self, *_):
        self._action_status.set_text("Starting tinyproxy (requires polkit auth)…")
        CommandRunner.run_shell(
            "systemctl start tinyproxy",
            lambda o, e, r: (self._action_status.set_text("Started." if r == 0 else f"Error: {e}"),
                              self._refresh_status()),
            use_sudo=True
        )

    def _stop_proxy(self, *_):
        self._action_status.set_text("Stopping tinyproxy…")
        CommandRunner.run_shell(
            "systemctl stop tinyproxy",
            lambda o, e, r: (self._action_status.set_text("Stopped." if r == 0 else f"Error: {e}"),
                              self._refresh_status()),
            use_sudo=True
        )

    def _load_blocklist(self, *_):
        # B-01 FIX: Read the filter file directly in Python — no shell involvement
        import os
        try:
            if os.path.exists(FILTER_FILE):
                with open(FILTER_FILE, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
            else:
                content = '# Blocklist empty or file missing'
        except OSError as e:
            content = f'# Could not read blocklist: {e}'
        self._bl_buf.set_text(content)

    def _save_blocklist(self, *_):
        start = self._bl_buf.get_start_iter()
        end   = self._bl_buf.get_end_iter()
        content = self._bl_buf.get_text(start, end, True)
        # Write via pkexec tee
        self._action_status.set_text("Saving blocklist (requires polkit auth)…")
        def _write():
            try:
                proc = subprocess.run( # nosec B603
                    ["/usr/bin/pkexec", "tee", FILTER_FILE],
                    input=content, text=True,
                    capture_output=True, timeout=30
                )
                GLib.idle_add(
                    self._action_status.set_text,
                    "Blocklist saved." if proc.returncode == 0 else f"Error: {proc.stderr}"
                )
            except Exception as e:
                GLib.idle_add(self._action_status.set_text, f"Error: {e}")
        threading.Thread(target=_write, daemon=True).start()

    def _quick_add(self, *_):
        domain = self._quick_entry.get_text().strip()
        if not domain:
            return

        if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
            self._action_status.set_text("Invalid domain format.")
            return

        self._action_status.set_text(f"Adding {domain} to blocklist…")

        # B-01 FIX: append domain via Python write (read current, append, write back)
        # Uses pkexec tee with the domain passed via stdin (no shell interpolation).
        import threading
        def _append():
            try:
                proc = subprocess.run(  # nosec B603 — list-form, domain via stdin
                    ["/usr/bin/pkexec", "tee", "-a", FILTER_FILE],
                    input=domain + "\n",
                    text=True,
                    capture_output=True,
                    timeout=15
                )
                if proc.returncode == 0:
                    subprocess.run(  # nosec B603 — list-form
                        ["/usr/bin/pkexec", "systemctl", "restart", "tinyproxy"],
                        timeout=15
                    )
                    GLib.idle_add(self._action_status.set_text, f"Added {domain}.")
                    GLib.idle_add(self._load_blocklist)
                else:
                    GLib.idle_add(self._action_status.set_text,
                                  f"Error: {proc.stderr}")
            except Exception as e:
                GLib.idle_add(self._action_status.set_text, f"Error: {e}")

        threading.Thread(target=_append, daemon=True).start()
        self._quick_entry.set_text("")

    def _auto_update(self, *_):
        self._action_status.set_text("Downloading Steven Black hosts list…")

        # B-04: Maximum download size (50 MB) to prevent DoS via huge response
        MAX_BYTES = 50 * 1024 * 1024
        # Domain regex for per-entry validation before writing
        _DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+$")

        def _worker():
            try:
                import urllib.request
                if not HOSTS_URL.startswith("https://"):
                    raise ValueError("HTTPS scheme required")
                req = urllib.request.Request(HOSTS_URL)
                with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                    raw_bytes = resp.read(MAX_BYTES + 1)

                # B-04: Reject oversized responses
                if len(raw_bytes) > MAX_BYTES:
                    GLib.idle_add(self._action_status.set_text,
                                  "Update aborted: response exceeded 50 MB size limit.")
                    return

                raw = raw_bytes.decode('utf-8', errors='replace')

                # Extract and validate each domain before including it
                domains = []
                for line in raw.splitlines():
                    parts = line.split()
                    if (
                        line.startswith("0.0.0.0")
                        and len(parts) >= 2
                        and parts[1] not in ("0.0.0.0", "localhost", "localhost.localdomain")
                        and _DOMAIN_RE.match(parts[1])  # B-04: per-domain validation
                    ):
                        domains.append(parts[1])

                content = "\n".join(domains) + "\n"
                proc = subprocess.run(  # nosec B603 — list-form
                    ["/usr/bin/pkexec", "tee", FILTER_FILE],
                    input=content, text=True,
                    capture_output=True, timeout=30
                )
                if proc.returncode == 0:
                    subprocess.run(["/usr/bin/pkexec", "systemctl", "restart", "tinyproxy"],  # nosec B603
                                   timeout=15)
                    GLib.idle_add(self._action_status.set_text,
                                  f"Blocklist updated: {len(domains):,} domains blocked.")
                    GLib.idle_add(self._load_blocklist)
                else:
                    GLib.idle_add(self._action_status.set_text, f"Error saving: {proc.stderr}")
            except Exception as e:
                GLib.idle_add(self._action_status.set_text, f"Update failed: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    def _tail_log(self, *_):
        self._log_buf.set_text("Loading log…")
        CommandRunner.run_shell(
            f"tail -n 50 {LOG_FILE} 2>/dev/null || echo 'Log file not found: {LOG_FILE}'",
            lambda o, e, r: self._log_buf.set_text(o or e or "(empty log)")
        )
