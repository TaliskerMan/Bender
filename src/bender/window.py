# Bender — Main Application Window
# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# Licensed under GPLv3 or later

import importlib.metadata
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .tab_system import SystemTab
from .tab_security import SecurityTab
from .tab_network import NetworkTab
from .tab_maintenance import MaintenanceTab
from .tab_weather import WeatherTab
from .tab_proxy import ProxyTab


class BenderWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Bender")
        self.set_default_size(960, 700)

        # ── Root layout ──────────────────────────────────────────────────────
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root_box)

        # ── Header bar ───────────────────────────────────────────────────────
        header = Adw.HeaderBar()
        header.set_centering_policy(Adw.CenteringPolicy.STRICT)

        # Title widget — ViewSwitcher (top bar navigation)
        self.stack = Adw.ViewStack()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)

        # Hamburger menu
        menu = Gio.Menu()
        theme_section = Gio.Menu()
        theme_section.append("System Theme", "win.theme-system")
        theme_section.append("Light Mode",   "win.theme-light")
        theme_section.append("Dark Mode",    "win.theme-dark")
        menu.append_section("Appearance", theme_section)

        about_section = Gio.Menu()
        about_section.append("About Bender", "win.about")
        menu.append_section(None, about_section)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        root_box.append(header)

        # ── Theme actions ─────────────────────────────────────────────────────
        for name, scheme in [
            ("theme-system", Adw.ColorScheme.DEFAULT),
            ("theme-light",  Adw.ColorScheme.FORCE_LIGHT),
            ("theme-dark",   Adw.ColorScheme.FORCE_DARK),
        ]:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _a, _p, s=scheme: self._set_theme(s))
            self.add_action(action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        # ── ViewStack pages ───────────────────────────────────────────────────
        pages = [
            ("system",      "computer-symbolic",         "System",      SystemTab()),
            ("security",    "security-high-symbolic",    "Security",    SecurityTab()),
            ("network",     "network-wired-symbolic",    "Network",     NetworkTab()),
            ("maintenance", "emblem-system-symbolic",    "Maintenance", MaintenanceTab()),
            ("weather",     "weather-clear-symbolic",    "Weather",     WeatherTab()),
            ("proxy",       "network-vpn-symbolic",      "Proxy",       ProxyTab()),
        ]
        for name, icon, title, widget in pages:
            page = self.stack.add_titled(widget, name, title)
            page.set_icon_name(icon)

        root_box.append(self.stack)

        # ── Bottom switcher bar (for narrower windows) ────────────────────────
        bar = Adw.ViewSwitcherBar(stack=self.stack)
        bar.set_reveal(True)
        root_box.append(bar)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_theme(self, scheme):
        Adw.StyleManager.get_default().set_color_scheme(scheme)

    def _on_about(self, _action, _param):
        try:
            version = importlib.metadata.version('bender')
        except importlib.metadata.PackageNotFoundError:
            version = "dev"

        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Bender",
            application_icon="com.taliskerman.bender",
            developer_name="Chuck Talk",
            version=version,
            comments="Linux workstation dashboard — Bite my shiny metal app!",
            website="https://github.com/TaliskerMan/Bender",
            copyright="© 2026 Chuck Talk &lt;chuck@nordheim.online&gt;",
            license_type=Gtk.License.GPL_3_0,
        )
        # Legal blurb shown under the license button
        about.set_license(
            "This program is free software: you can redistribute it and/or modify it "
            "under the terms of the GNU General Public License as published by the "
            "Free Software Foundation, either version 3 of the License, or "
            "(at your option) any later version.\n\n"
            "This program is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the "
            "GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public License "
            "along with this program. If not, see https://www.gnu.org/licenses/."
        )
        about.present()
