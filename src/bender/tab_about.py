# Bender — About Tab
# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# Licensed under GPLv3 or later

import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
# Import package version per CP-AutoIncrement
from . import __version__


def get_about_heading() -> str:
    """Return the canonical About heading with version and contact attribution."""
    return (
        f"Bender v{__version__} — Bite my shiny metal app!\n"
        "Copyright Chuck Talk <chuck@nordheim.online>, a Nordheim Online Product.\n"
        "Support: support@nordheim.online"
    )


def get_license_text() -> str:
    """Return the GPLv3 license text from disk or the canonical fallback notice."""
    try:
        license_path = os.path.join(os.path.dirname(__file__), '../../LICENSE')
        if not os.path.exists(license_path):
            license_path = '/usr/share/bender/LICENSE'
        with open(license_path, 'r', encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return "GNU General Public License v3.0\nSee https://www.gnu.org/licenses/gpl-3.0.html"


class AboutTab(Gtk.Box):
    """
    AboutTab displays product identity, developer attribution,
    and the GNU GPL v3 license text.
    """
    def __init__(self):
        """
        Initializes the About tab with the project logo, name,
        and scrolled license view.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                        margin_top=24, margin_bottom=24,
                        margin_start=24, margin_end=24)
        scroll.set_child(inner)
        self.append(scroll)

        # ── Logos (Centered) ─────────────────────────────────────────────────
        logos_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        logos_hbox.set_halign(Gtk.Align.CENTER)

        bender_icon = Gtk.Image.new_from_icon_name("com.taliskerman.bender")
        bender_icon.set_pixel_size(96)
        logos_hbox.append(bender_icon)

        try:
            img_path = os.path.join(os.path.dirname(__file__), '../../data/noln_ui.png')
            if not os.path.exists(img_path):
                img_path = '/usr/share/bender/data/noln_ui.png'
            noln_img = Gtk.Image.new_from_file(img_path)
            noln_img.set_pixel_size(96)
        except Exception:
            noln_img = Gtk.Image()

        link_btn = Gtk.LinkButton(uri="https://nordheim.online")
        link_btn.set_child(noln_img)
        logos_hbox.append(link_btn)

        inner.append(logos_hbox)

        # ── Heading / Title ──────────────────────────────────────────────────
        # Display version and contact email per CP-AboutPage and CP-AutoIncrement
        lbl = Gtk.Label(
            label=get_about_heading(),
            xalign=0
        )
        lbl.set_wrap(True)
        lbl.add_css_class("title-2")
        inner.append(lbl)

        # ── License Text ─────────────────────────────────────────────────────
        tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        tv.add_css_class("monospace")
        buf = tv.get_buffer()
        buf.set_text(get_license_text())

        license_sw = Gtk.ScrolledWindow(vexpand=True)
        license_sw.set_child(tv)
        inner.append(license_sw)
