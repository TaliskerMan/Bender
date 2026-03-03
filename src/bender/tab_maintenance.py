# Bender — Maintenance Tab
# System update, Flatpak update, clear shared memory, clean logs, GNOME reset, temp cleanup.

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner


ACTIONS = [
    {
        "label":    "System Update (nala)",
        "subtitle": "Update package lists and upgrade all packages",
        "icon":     "software-update-available-symbolic",
        "cmd":      "nala update && nala upgrade",
        "sudo":     True,
    },
    {
        "label":    "Flatpak Update",
        "subtitle": "Update all installed Flatpak applications",
        "icon":     "package-x-generic-symbolic",
        "cmd":      "flatpak update -y 2>&1 || echo 'flatpak not installed'",
        "sudo":     False,
    },
    {
        "label":    "Clear Shared Memory (/dev/shm)",
        "subtitle": "Remove stale files from the shared memory filesystem",
        "icon":     "edit-clear-symbolic",
        "cmd":      "find /dev/shm -maxdepth 1 -type f -delete -print && echo 'Shared memory cleared.'",
        "sudo":     True,
    },
    {
        "label":    "Clean Rotated Logs (.gz)",
        "subtitle": "Delete compressed rotated log archives from /var/log",
        "icon":     "user-trash-symbolic",
        "cmd":      "find /var/log -name '*.gz' -type f -delete -print && echo 'Old logs cleaned.'",
        "sudo":     True,
    },
    {
        "label":    "Clean Temp Files (/tmp)",
        "subtitle": "Remove stale qipc* and gdm* temp files",
        "icon":     "folder-templates-symbolic",
        "cmd":      (
            "find /tmp -maxdepth 1 -name 'qipc*' -delete -print; "
            "find /tmp -maxdepth 1 -name 'gdm*'  -delete -print; "
            "echo 'Temp cleanup done.'"
        ),
        "sudo":     False,
    },
    {
        "label":    "Reset GNOME App Grid",
        "subtitle": "Reset app-picker-layout and restart GNOME session",
        "icon":     "view-grid-symbolic",
        "cmd":      "gsettings reset org.gnome.shell app-picker-layout && sleep 1 && gnome-session-quit --no-prompt",
        "sudo":     False,
    },
]


class _ActionRow(Adw.ActionRow):
    def __init__(self, action: dict):
        super().__init__(
            title=action["label"],
            subtitle=action["subtitle"],
        )
        self.set_icon_name(action["icon"])
        self._action = action

        # Run button as suffix
        self._btn = Gtk.Button(label="Run", valign=Gtk.Align.CENTER)
        self._btn.add_css_class("suggested-action")
        self._btn.connect("clicked", self._run)
        self.add_suffix(self._btn)

        # Spinner
        self._spinner = Gtk.Spinner(valign=Gtk.Align.CENTER)
        self.add_suffix(self._spinner)

        # Expandable output log below the row  (attached via parent box)
        self._exp = Gtk.Expander(label="Output", margin_start=16, margin_end=16, margin_bottom=4)
        self._tv = Gtk.TextView(editable=False, cursor_visible=False,
                                wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._tv.add_css_class("monospace")
        self._buf = self._tv.get_buffer()
        sw = Gtk.ScrolledWindow(min_content_height=80, vexpand=False)
        sw.set_child(self._tv)
        self._exp.set_child(sw)

    @property
    def expander(self):
        return self._exp

    def _run(self, _btn):
        self._btn.set_sensitive(False)
        self._spinner.start()
        self._buf.set_text("Running…")
        self._exp.set_expanded(True)
        CommandRunner.run_shell(
            self._action["cmd"],
            self._on_done,
            use_sudo=self._action["sudo"]
        )

    def _on_done(self, out, err, rc):
        self._btn.set_sensitive(True)
        self._spinner.stop()
        self._buf.set_text(out or err or "(no output)")


class MaintenanceTab(Gtk.Box):
    def __init__(self):
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
        outer.append(group)

        for action in ACTIONS:
            row = _ActionRow(action)
            group.add(row)
            # Attach the expander widget directly below the group
            outer.append(row.expander)
