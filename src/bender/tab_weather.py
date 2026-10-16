# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU GPL v3 for details.

# Bender — Weather Tab
# Fetches weather by wrapping the ansiweather CLI utility, which gets its data
# from OpenWeatherMap. Nothing is fetched until the user asks: the location is
# sent to OpenWeatherMap, so Bender must not do that on its own at start-up.

import json
import os
import re

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .runner import CommandRunner
from .validators import is_valid_city


def _settings_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "bender", "weather.json")


def load_weather_settings() -> dict:
    """The last location and unit the user fetched, or defaults."""
    try:
        with open(_settings_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        location = data.get("location", "")
        metric = bool(data.get("metric", False))
        if location and not is_valid_city(location):
            location = ""
        return {"location": location, "metric": metric}
    except (OSError, ValueError, AttributeError):
        return {"location": "", "metric": False}


def save_weather_settings(location: str, metric: bool) -> None:
    """Remember the location (kept only on this computer, readable only by you)."""
    path = _settings_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"location": location, "metric": metric}, fh)
    except OSError:
        pass


class WeatherTab(Gtk.Box):
    """
    WeatherTab wraps the ansiweather CLI utility to query and display weather forecasts.
    """
    def __init__(self):
        """
        Initializes the weather panel, validating command availability, laying stdout_text 
        inputs (city and unit selectors), and fetching the initial forecast.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._use_metric = False

        scroll = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                        margin_top=16, margin_bottom=16,
                        margin_start=20, margin_end=20)
        scroll.set_child(inner)
        self.append(scroll)

        # ── Check if ansiweather is installed ─────────────────────────────────
        if not CommandRunner.command_exists("ansiweather"):
            banner = Adw.StatusPage(
                title="Ansiweather Not Installed",
                description="Install ansiweather to use the Weather tab.\nsudo apt install ansiweather",
                icon_name="weather-clear-symbolic",
            )
            inner.append(banner)
            return

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        inner.append(ctrl)

        city_lbl = Gtk.Label(label="Location:")
        city_lbl.add_css_class("dim-label")
        ctrl.append(city_lbl)

        settings = load_weather_settings()
        self._city_entry = Gtk.Entry(
            text=settings["location"],
            placeholder_text="City,State,Country — e.g. Austin,TX,USA",
            hexpand=True,
        )
        # Fetch when enter is pressed
        self._city_entry.connect("activate", self._fetch)
        ctrl.append(self._city_entry)

        # Temperature Unit Dropdown
        self._unit_dropdown = Gtk.DropDown.new_from_strings(["°F (Imperial)", "°C (Metric)"])
        self._unit_dropdown.set_selected(1 if settings["metric"] else 0)
        self._unit_dropdown.connect("notify::selected", self._on_unit_changed)
        ctrl.append(self._unit_dropdown)

        fetch_btn = Gtk.Button(label="Get Weather")
        fetch_btn.add_css_class("suggested-action")
        fetch_btn.connect("clicked", self._fetch)
        ctrl.append(fetch_btn)

        privacy = Gtk.Label(
            label="The location you enter is sent to OpenWeatherMap (through "
                  "ansiweather) when you click Get Weather.",
            xalign=0, wrap=True,
        )
        privacy.add_css_class("dim-label")
        inner.append(privacy)

        # ── Output Area ───────────────────────────────────────────────────────
        self._output_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12)
        inner.append(self._output_box)

        # We'll use a large centered label for the status and output
        self._status_lbl = Gtk.Label(
            label="Enter a location and click Get Weather.",
            wrap=True, justify=Gtk.Justification.CENTER)
        self._status_lbl.add_css_class("title-3")
        self._status_lbl.set_margin_top(20)
        self._output_box.append(self._status_lbl)

        # And a monospaced view for the raw CLI output for reliability
        tv_box = Gtk.Box(margin_top=20, hexpand=True)
        tv_frame = Gtk.Frame(hexpand=True)
        self._tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR, hexpand=True)
        self._tv.add_css_class("monospace")
        self._tv.set_margin_top(12)
        self._tv.set_margin_bottom(12)
        self._tv.set_margin_start(12)
        self._tv.set_margin_end(12)
        self._buf = self._tv.get_buffer()
        tv_frame.set_child(self._tv)
        tv_box.append(tv_frame)
        self._output_box.append(tv_box)


    def _fetch(self, *_):
        """
        Initiates a background fetch via ansiweather for the entered location and unit type.
        Validates the city input to prevent injection characters.
        """
        city = self._city_entry.get_text().strip()
        if not city:
            return
            
        if not is_valid_city(city):
            self._status_lbl.set_text("Invalid location format.")
            self._buf.set_text("Use only letters, digits, spaces, commas, dots and underscores.")
            return

        metric = self._unit_dropdown.get_selected() == 1
        unit = "metric" if metric else "imperial"
        save_weather_settings(city, metric)
        self._status_lbl.set_text(f"Fetching weather for {city}...")
        self._buf.set_text("Loading...")
        
        # Example command: ansiweather -l Austin,TX,USA -u imperial -s true -f 3 -d true -a false
        # We quote the city to prevent injection, though runner.run uses list args safely anyway.
        # But we'll construct the list arguments directly for maximum safety:
        cmd = ["ansiweather", "-l", city, "-u", unit, "-s", "true", "-f", "7", "-d", "true", "-a", "false"]
        CommandRunner.run(cmd, self._on_done)

    def _on_done(self, stdout_text, stderr_text, return_code):
        """
        Callback handler executed when the ansiweather command completes.
        Strips ANSI codes, parses multi-day forecast lists, and displays formatted results.
        """
        if return_code != 0:
            self._status_lbl.set_text("Failed to fetch weather.")
            self._buf.set_text(stderr_text or stdout_text or "Unknown error.")
            return

        text = stdout_text.strip()
        # Clean up ANSI escape codes if any snuck through (though -a false should stop them)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Raw text backup in the textview below
        self._buf.set_text(text)
        
        # Try to parse the multi-day forecast nicely for the centered label
        if "forecast:" in text:
            # format is "City forecast: Day 1... - Day 2... - Day 3..."
            # Let's split by " - " to get individual days
            parts = text.split(" - ")
            
            # The first part usually contains "City forecast: "
            # Let's clean it up to just be a stacked list of days
            if len(parts) > 0:
                header_split = parts[0].split("forecast:")
                if len(header_split) == 2:
                    header = header_split[0].strip() + " forecast:"
                    days = [header_split[1].strip()] + parts[1:]
                else:
                    header = "Forecast:"
                    days = parts
                
                formatted_forecast = header + "\n\n" + "\n".join(d.strip() for d in days)
                self._status_lbl.set_text(formatted_forecast)
            else:
                self._status_lbl.set_text(text)
        else:
             self._status_lbl.set_text(text)

    def _on_unit_changed(self, dropdown, pspec):
        """
        Re-fetches in the new unit, but only if a location has been entered:
        changing the unit must not send anything on its own.
        """
        if self._city_entry.get_text().strip():
            self._fetch()
