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
    """
    Main Libadwaita Application class for Bender.
    
    Coordinates the application lifecycle, including window instantiation,
    loading custom icon assets in development environments, and teardown operations.
    """
    def __init__(self):
        """
        Initializes the Adw.Application with the specific com.taliskerman.bender ID.
        """
        super().__init__(
            application_id='com.taliskerman.bender',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None

    def do_activate(self):
        """
        Triggers window creation and display when the application is activated.
        """
        if not self.window:
            self.window = BenderWindow(self)
        self.window.present()

    def do_startup(self):
        """
        Performs application initialization tasks.
        
        This sets up custom application icon resource paths for the GTK IconTheme 
        if running in local development mode, and configures the default color 
        scheme to respect the user's system preferences.
        """
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
        """
        Cleans up resources and shuts down the application.
        """
        Adw.Application.do_shutdown(self)


def setup_logging():
    """
    Configures application-wide logging.
    
    Creates a dedicated log directory at ~/.local/state/bender/ and pipes
    logs to both bender.log and standard stdout.
    """
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
    """
    The main execution entry point for the bender binary script.
    
    Sets up logging, binds SIGINT signal handlers for clean terminal termination,
    and runs the application loop.
    """
    setup_logging()
    app = BenderApp()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, app.quit)
    return app.run(sys.argv)



if __name__ == '__main__':
    main()
