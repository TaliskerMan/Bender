# Bender — About Tab

import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class AboutTab(Gtk.Box):
    """AboutTab implementation."""
    def __init__(self):
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
        lbl = Gtk.Label(label="Bender, Bite my shiny metal app! Copyright Chuck Talk, a Nordheim Online Product.", xalign=0)
        lbl.set_wrap(True)
        lbl.add_css_class("title-2")
        inner.append(lbl)

        # ── License Text ─────────────────────────────────────────────────────
        tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        tv.add_css_class("monospace")
        buf = tv.get_buffer()

        try:
            license_path = os.path.join(os.path.dirname(__file__), '../../LICENSE')
            if not os.path.exists(license_path):
                license_path = '/usr/share/bender/LICENSE'
            with open(license_path, 'r', encoding='utf-8') as f:
                license_text = f.read()
        except Exception:
            license_text = "GNU General Public License v3.0\nSee https://www.gnu.org/licenses/gpl-3.0.html"

        buf.set_text(license_text)

        license_sw = Gtk.ScrolledWindow(vexpand=True)
        license_sw.set_child(tv)
        inner.append(license_sw)
