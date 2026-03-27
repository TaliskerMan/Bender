# Bender — Linux Workstation Dashboard
# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# Licensed under GPLv3 or later

import sys
import signal
import gi
import logging
import os
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from .window import BenderWindow


class BenderApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='com.taliskerman.bender',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = BenderWindow(self)
        self.window.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        
        # In dev mode, GTK needs to know where our local icons are
        import os
        from gi.repository import Gdk
        _src_dir = os.path.dirname(os.path.abspath(__file__))
        _icons_dir = os.path.normpath(os.path.join(_src_dir, '..', '..', 'data', 'icons'))
        if os.path.isdir(_icons_dir):
            display = Gdk.Display.get_default()
            if display:
                theme = Gtk.IconTheme.get_for_display(display)
                theme.add_search_path(_icons_dir)

        # Respect system theme preference by default
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT)

    def do_shutdown(self):
        Adw.Application.do_shutdown(self)


def setup_logging():
    log_dir = Path.home() / ".local" / "state" / "bender"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bender.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Bender initialized")

def main():
    setup_logging()
    app = BenderApp()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, app.quit)
    return app.run(sys.argv)


if __name__ == '__main__':
    main()
