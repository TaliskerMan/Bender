# Bender — Security Audit Tab
# Runs security checks drawn from Menul8.sh, eff0.sh, badperms.sh, lastchk.sh, killz.sh, sxid.sh

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner


# ── Per-check data ────────────────────────────────────────────────────────────
CHECKS = [
    {
        "id":    "uid0",
        "label": "UID-0 & Sudo Users",
        "icon":  "system-users-symbolic",
        "cmd":   (
            "echo '--- Users with UID 0 ---' && "
            "awk -F: '$3==0{print $1}' /etc/passwd && "
            "echo '' && echo '--- Sudo group members ---' && "
            "getent group sudo | cut -d: -f4 | tr ',' '\\n'"
        ),
        "sudo":  False,
    },
    {
        "id":    "badperms",
        "label": "World-Writable Files (777)",
        "icon":  "dialog-warning-symbolic",
        "cmd":   "find / -xdev -type f -perm 777 2>/dev/null | head -50",
        "sudo":  False,
    },
    {
        "id":    "suid",
        "label": "SUID / SGID Files",
        "icon":  "security-medium-symbolic",
        "cmd":   "find /usr/bin /usr/sbin /bin /sbin -type f \\( -perm -4000 -o -perm -2000 \\) -ls 2>/dev/null",
        "sudo":  False,
    },
    {
        "id":    "newusers",
        "label": "Recent User Accounts",
        "icon":  "avatar-default-symbolic",
        "cmd":   (
            "echo '--- All login-shell users ---' && "
            "grep -E '/(bash|sh|zsh|fish)$' /etc/passwd | cut -d: -f1,3,5 | column -t -s:"
        ),
        "sudo":  False,
    },
    {
        "id":    "zombies",
        "label": "Zombie Processes",
        "icon":  "process-stop-symbolic",
        "cmd":   "ps aux | awk '$8~/^[Zz]/{print \"PID:\"$2, \"PPID:\"$3, \"USER:\"$1, \"CMD:\"$11}' || echo 'No zombies found'",
        "sudo":  False,
    },
    {
        "id":    "logins",
        "label": "Recent Login Audit",
        "icon":  "document-open-recent-symbolic",
        "cmd":   "last -n 20 -d -w",
        "sudo":  False,
    },
    {
        "id":    "hidden",
        "label": "Hidden Processes (unhide)",
        "icon":  "find-location-symbolic",
        "cmd":   "unhide procall 2>/dev/null || echo 'unhide not installed — run: sudo apt install unhide'",
        "sudo":  True,
    },
]


class _CheckRow(Gtk.Box):
    """A single check row: icon | label | status badge | Run button."""

    def __init__(self, check: dict, output_buf):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._check = check
        self._buf = output_buf

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                      margin_top=6, margin_bottom=6,
                      margin_start=12, margin_end=12)
        self.append(top)

        icon = Gtk.Image(icon_name=check["icon"])
        top.append(icon)

        lbl = Gtk.Label(label=check["label"], xalign=0, hexpand=True)
        top.append(lbl)

        self._badge = Gtk.Label(label="–")
        self._badge.add_css_class("dim-label")
        top.append(self._badge)

        self._run_btn = Gtk.Button(label="Run")
        self._run_btn.connect("clicked", self._run)
        top.append(self._run_btn)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

    def _run(self, _btn=None):
        self._badge.set_text("⏳")
        self._run_btn.set_sensitive(False)
        
        end_iter = self._buf.get_end_iter()
        self._buf.insert(end_iter, f"\n--- Security Check: {self._check['label']} ---\nRunning...\n")
        
        CommandRunner.run_shell(self._check["cmd"], self._on_done,
                                use_sudo=self._check["sudo"])

    def _on_done(self, out, err, rc):
        self._run_btn.set_sensitive(True)
        result = out or err or "(no output)"
        
        end_iter = self._buf.get_end_iter()
        self._buf.insert(end_iter, f"{result}\n")
        
        if rc == 0:
            if not out.strip() or "No" in out or out.strip() == "":
                self._badge.set_text("✅")
            else:
                self._badge.set_text("⚠️")
        else:
            self._badge.set_text("❌")

    def run(self):
        """Called programmatically by Run All."""
        self._run()


class SecurityTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # ── Header strip ──────────────────────────────────────────────────────
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                         margin_top=12, margin_bottom=8,
                         margin_start=16, margin_end=16)
        self.append(header)

        title = Gtk.Label(label="Security Audit", xalign=0, hexpand=True)
        title.add_css_class("title-2")
        header.append(title)

        run_all_btn = Gtk.Button(label="▶  Run All Checks")
        run_all_btn.add_css_class("suggested-action")
        run_all_btn.connect("clicked", self._run_all)
        header.append(run_all_btn)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        # ── Scrollable check list ─────────────────────────────────────────────
        scroll = Gtk.ScrolledWindow(vexpand=True)
        checks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scroll.set_child(checks_box)
        self.append(scroll)

        # ── Global Terminal ──────────────────────────────────────────────────
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=16, margin_bottom=8)
        
        term_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        terminal_label = Gtk.Label(label="Global Security Output", xalign=0, hexpand=True)
        terminal_label.add_css_class("heading")
        term_header.append(terminal_label)
        
        clear_btn = Gtk.Button(label="Clear", valign=Gtk.Align.CENTER)
        clear_btn.connect("clicked", self._clear_terminal)
        term_header.append(clear_btn)
        
        terminal_box.append(term_header)

        self._console_tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._console_tv.add_css_class("monospace")
        self._console_buf = self._console_tv.get_buffer()
        
        sw_term = Gtk.ScrolledWindow(vexpand=True, min_content_height=200)
        sw_term.set_child(self._console_tv)
        terminal_box.append(sw_term)

        self.append(terminal_box)

        self._rows: list[_CheckRow] = []
        for check in CHECKS:
            row = _CheckRow(check, self._console_buf)
            checks_box.append(row)
            self._rows.append(row)

    def _clear_terminal(self, _btn):
        self._console_buf.set_text("")

    def _run_all(self, _btn):
        for row in self._rows:
            row.run()
