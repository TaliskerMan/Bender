# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — Proxy Manager Tab
# Manages tinyproxy: start/stop, blocklist management, live logs, auto-update.

import collections
import subprocess
import shutil
import threading

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from .runner import CommandRunner
from .validators import (
    TINYPROXY_CONF,
    is_valid_domain,
    merge_blocklists,
    parse_hosts_blocklist,
    parse_tinyproxy_conf,
)


FILTER_FILE = "/etc/tinyproxy/filter"   # used when tinyproxy.conf names none
LOG_FILE    = "/var/log/tinyproxy/tinyproxy.log"
HOSTS_URL   = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

# Root-side writers. The filter path arrives as "$1" and the text on stdin, so
# nothing is ever pasted into the script. try-restart restarts tinyproxy only
# if it is already running (it never starts a proxy the user has stopped), so
# the change takes effect straight away.
_WRITE_SCRIPT  = 'cat > "$1" && systemctl try-restart tinyproxy'
_APPEND_SCRIPT = 'cat >> "$1" && systemctl try-restart tinyproxy'


def read_tinyproxy_settings() -> dict:
    """Settings from tinyproxy.conf, or defaults if it can't be read."""
    try:
        with open(TINYPROXY_CONF, encoding="utf-8", errors="replace") as fh:
            settings = parse_tinyproxy_conf(fh.read())
        settings["conf_readable"] = True
    except OSError:
        settings = {"filter": None, "port": None, "conf_readable": False}
    return settings


def read_log_tail(path: str = LOG_FILE, lines: int = 50) -> str:
    """The last *lines* lines of the tinyproxy log, or why they can't be shown."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tail = collections.deque(fh, maxlen=lines)
        return "".join(tail) or "(the log is empty)"
    except FileNotFoundError:
        return f"No log yet: {path} doesn't exist (tinyproxy creates it when it runs)."
    except PermissionError:
        return (f"You don't have permission to read {path}. On Debian and Ubuntu "
                "it is readable by members of the 'adm' group.")
    except OSError as error:
        return f"Could not read {path}: {error.strerror}"


class ProxyTab(Gtk.Box):
    """
    ProxyTab manages the Tinyproxy daemon. Features control buttons to start/stop
    the service, blocklist editing, auto-updates from external hosts lists, and log tails.
    """
    def __init__(self):
        """
        Initializes the Proxy manager interface, checking if tinyproxy is installed,
        setting up status headers, controls, editors, and consoles.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._log_tail_proc = None
        self._settings = read_tinyproxy_settings()
        # Edit the file tinyproxy actually reads, if its config names one.
        self._filter_file = self._settings["filter"] or FILTER_FILE
        self._blocklist_readable = False

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

        # ── Is the blocklist actually used? ───────────────────────────────────
        # tinyproxy ships with its Filter line commented out, and then ignores
        # the blocklist completely. Say so rather than imply it's blocking.
        if self._settings["filter"] is None:
            if self._settings["conf_readable"]:
                text = ("⚠️  The blocklist isn't active. Tinyproxy only uses it when "
                        f"{TINYPROXY_CONF} contains the line:\n"
                        f'    Filter "{FILTER_FILE}"\n'
                        "Add that line (as administrator), then restart the proxy.")
            else:
                text = (f"⚠️  Couldn't read {TINYPROXY_CONF}, so Bender can't tell "
                        "whether the blocklist is active. Tinyproxy only uses it "
                        f'when that file contains a line such as: Filter "{FILTER_FILE}"')
            warn = Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)
            warn.add_css_class("warning")
            inner.append(warn)

        port = self._settings["port"] or 8888
        scope = Gtk.Label(
            label=f"Only programs set to use the proxy (127.0.0.1, port {port}) "
                  "are filtered. Blocklist file: " + self._filter_file,
            xalign=0, wrap=True,
        )
        scope.add_css_class("dim-label")
        inner.append(scope)

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

        self._save_btn = Gtk.Button(label="Save Blocklist")
        self._save_btn.add_css_class("suggested-action")
        self._save_btn.connect("clicked", self._save_blocklist)
        bl_ctrl.append(self._save_btn)

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

        log_lbl = Gtk.Label(label="📋  Proxy Log", xalign=0, hexpand=True)
        log_lbl.add_css_class("heading")
        log_hdr.append(log_lbl)

        self._log_tv = Gtk.TextView(editable=False, cursor_visible=False,
                                   wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._log_tv.add_css_class("monospace")
        self._log_buf = self._log_tv.get_buffer()
        log_sw = Gtk.ScrolledWindow(vexpand=True, min_content_height=120)
        log_sw.set_child(self._log_tv)
        inner.append(log_sw)

        tail_btn = Gtk.Button(label="Show Last 50 Lines")
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
        """
        Checks the status of the local tinyproxy service via systemctl.
        """
        self._status_badge.set_text("⏳ Checking…")
        CommandRunner.run_shell(
            "systemctl is-active tinyproxy",
            self._on_status
        )

    def _on_status(self, stdout_text, stderr_text, return_code):
        """
        Callback updating the status indicator label depending on service state.
        """
        if stdout_text.strip() == "active":
            self._status_badge.set_text("🟢  Active")
        else:
            self._status_badge.set_text("🔴  Inactive")

    def _start_proxy(self, *_):
        """
        Starts the tinyproxy service (requires polkit/pkexec authentication).
        """
        self._action_status.set_text("Starting tinyproxy (requires polkit auth)…")
        CommandRunner.run(
            ["systemctl", "start", "tinyproxy"],
            lambda stdout, stderr, return_code: (self._action_status.set_text("Started." if return_code == 0 else f"Error: {stderr}"),
                              self._refresh_status()),
            use_sudo=True
        )

    def _stop_proxy(self, *_):
        """
        Stops the tinyproxy service (requires polkit/pkexec authentication).
        """
        self._action_status.set_text("Stopping tinyproxy…")
        CommandRunner.run(
            ["systemctl", "stop", "tinyproxy"],
            lambda stdout, stderr, return_code: (self._action_status.set_text("Stopped." if return_code == 0 else f"Error: {stderr}"),
                              self._refresh_status()),
            use_sudo=True
        )

    def _load_blocklist(self, *_):
        """
        Reads the blocklist file into the editor.

        If the file exists but can't be read, Save is disabled: saving would
        otherwise replace the real blocklist with whatever the editor shows.
        """
        try:
            with open(self._filter_file, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            self._blocklist_readable = True
            message = ""
        except FileNotFoundError:
            content = ""
            self._blocklist_readable = True
            message = f"No blocklist yet; Save creates {self._filter_file}."
        except OSError as error:
            content = ""
            self._blocklist_readable = False
            message = (f"Can't read {self._filter_file} ({error.strerror}), so "
                       "Save is turned off to protect the existing list.")
        self._bl_buf.set_text(content)
        self._save_btn.set_sensitive(self._blocklist_readable)
        if message:
            self._action_status.set_text(message)

    def _run_root_writer(self, script: str, text: str, on_success):
        """
        Run a root-side writer (one password prompt) with *text* on stdin and
        the filter path as $1; report the result in the status line.
        """
        def _worker():
            try:
                proc = subprocess.run(  # nosec B603 — list-form; data via stdin/argv
                    ["/usr/bin/pkexec", "/bin/bash", "-c", script, "bash", self._filter_file],
                    input=text, text=True, capture_output=True, timeout=120,
                )
                if proc.returncode == 0:
                    GLib.idle_add(on_success)
                elif proc.returncode == 126:
                    GLib.idle_add(self._action_status.set_text,
                                  "Cancelled: the password prompt was dismissed.")
                else:
                    GLib.idle_add(self._action_status.set_text,
                                  f"Error: {proc.stderr.strip() or proc.returncode}")
            except Exception as error:
                GLib.idle_add(self._action_status.set_text, f"Error: {error}")
        threading.Thread(target=_worker, daemon=True).start()

    def _after_write(self, message: str):
        self._action_status.set_text(message)
        self._load_blocklist()

    def _save_blocklist(self, *_):
        """
        Saves the editor's text as the blocklist (requires polkit auth) and
        restarts tinyproxy if it is running, so the change applies now.
        """
        if not self._blocklist_readable:
            return
        start = self._bl_buf.get_start_iter()
        end   = self._bl_buf.get_end_iter()
        content = self._bl_buf.get_text(start, end, True)
        if content and not content.endswith("\n"):
            content += "\n"
        self._action_status.set_text("Saving blocklist (requires polkit auth)…")
        self._run_root_writer(_WRITE_SCRIPT, content,
                              lambda: self._after_write("Blocklist saved."))

    def _quick_add(self, *_):
        """
        Validates and appends a single domain to the blocklist, restarting
        tinyproxy if it is running.
        """
        domain = self._quick_entry.get_text().strip()
        if not domain:
            return

        if not is_valid_domain(domain):
            self._action_status.set_text("Invalid domain format.")
            return

        self._action_status.set_text(f"Adding {domain} to blocklist…")
        # Domain goes in via stdin, never through a shell.
        self._run_root_writer(_APPEND_SCRIPT, domain + "\n",
                              lambda: self._after_write(f"Added {domain}."))
        self._quick_entry.set_text("")

    def _auto_update(self, *_):
        """
        Asks whether to merge Steven Black's list into the blocklist or replace
        it (replacing removes domains the user added), then downloads it.
        """
        root = self.get_root()
        dialog = Adw.MessageDialog(
            transient_for=root if isinstance(root, Gtk.Window) else None,
            heading="Update from Steven Black's list?",
            body=("Bender downloads Steven Black's unified hosts list from GitHub "
                  "(tens of thousands of ad and tracking domains).\n\n"
                  "Merge keeps everything already in your blocklist and adds the "
                  "new domains. Replace removes your current list, including "
                  "domains you added yourself."),
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("replace", "Replace")
        dialog.add_response("merge", "Merge")
        dialog.set_response_appearance("replace", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_response_appearance("merge", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("merge")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_auto_update_response)
        dialog.present()

    def _on_auto_update_response(self, _dialog, response):
        if response not in ("merge", "replace"):
            return
        merge = response == "merge"
        if merge and not self._blocklist_readable:
            self._action_status.set_text(
                f"Can't merge: {self._filter_file} can't be read.")
            return
        existing = ""
        if merge:
            start = self._bl_buf.get_start_iter()
            existing = self._bl_buf.get_text(start, self._bl_buf.get_end_iter(), True)
        self._download_and_write(merge, existing)

    def _download_and_write(self, merge: bool, existing: str):
        """
        Downloads Steven Black's hosts file, keeps only valid domains, and
        writes them (merged or replacing) to the blocklist.
        """
        self._action_status.set_text("Downloading Steven Black hosts list…")

        # B-04: Maximum download size (50 MB) to prevent DoS via huge response
        MAX_BYTES = 50 * 1024 * 1024

        def _worker():
            try:
                import urllib.request
                if not HOSTS_URL.startswith("https://"):
                    raise ValueError("HTTPS scheme required")
                # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
                # Reviewed and accepted: HOSTS_URL is a module-level constant
                # pinned to an https:// address (see top of file), re-validated
                # on the line above, and no caller-controlled input reaches this
                # call. The file:// scheme abuse this rule warns about is not
                # reachable here. Semgrep flags it only because its dataflow
                # cannot prove a module global is constant.
                req = urllib.request.Request(HOSTS_URL)
                with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310 nosemgrep
                    raw_bytes = resp.read(MAX_BYTES + 1)

                # B-04: Reject oversized responses
                if len(raw_bytes) > MAX_BYTES:
                    GLib.idle_add(self._action_status.set_text,
                                  "Update aborted: response exceeded 50 MB size limit.")
                    return

                raw = raw_bytes.decode('utf-8', errors='replace')

                # Extract and validate each domain (see validators.parse_hosts_blocklist).
                domains = parse_hosts_blocklist(raw)
                if not domains:
                    GLib.idle_add(self._action_status.set_text,
                                  "Update aborted: the download contained no domains.")
                    return
                if merge:
                    content = merge_blocklists(existing, domains)
                    message = f"Blocklist merged: {len(domains):,} downloaded domains."
                else:
                    content = "\n".join(domains) + "\n"
                    message = f"Blocklist replaced: {len(domains):,} domains."
            except Exception as error:
                GLib.idle_add(self._action_status.set_text, f"Update failed: {error}")
                return
            GLib.idle_add(self._action_status.set_text,
                          "Saving blocklist (requires polkit auth)…")
            GLib.idle_add(self._run_root_writer, _WRITE_SCRIPT, content,
                          lambda: self._after_write(message))
        threading.Thread(target=_worker, daemon=True).start()

    def _tail_log(self, *_):
        """
        Shows the last 50 lines of the tinyproxy log, or why it can't.
        """
        self._log_buf.set_text(read_log_tail())
