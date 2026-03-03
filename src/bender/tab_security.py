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
    """A single check row: icon | label | status badge | Run button | expander output."""

    def __init__(self, check: dict):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._check = check

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

        # Output expander
        self._exp = Gtk.Expander(label="Output")
        self._exp.set_margin_start(12)
        self._exp.set_margin_end(12)
        self._exp.set_margin_bottom(4)

        self._tv = Gtk.TextView(editable=False, cursor_visible=False,
                                wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._tv.add_css_class("monospace")
        self._buf = self._tv.get_buffer()

        sw = Gtk.ScrolledWindow(vexpand=False, min_content_height=100)
        sw.set_child(self._tv)
        self._exp.set_child(sw)
        self.append(self._exp)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

    def _run(self, _btn=None):
        self._badge.set_text("⏳")
        self._run_btn.set_sensitive(False)
        self._exp.set_expanded(True)
        self._buf.set_text("Running…")
        CommandRunner.run_shell(self._check["cmd"], self._on_done,
                                use_sudo=self._check["sudo"])

    def _on_done(self, out, err, rc):
        self._run_btn.set_sensitive(True)
        result = out or err or "(no output)"
        self._buf.set_text(result)
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

        self._rows: list[_CheckRow] = []
        for check in CHECKS:
            row = _CheckRow(check)
            checks_box.append(row)
            self._rows.append(row)

    def _run_all(self, _btn):
        for row in self._rows:
            row.run()
