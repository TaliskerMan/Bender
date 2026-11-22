# Bender — Linux Workstation Dashboard
# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# Licensed under GPLv3 or later

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import signal
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, GLib, Gtk
from .validators import resolve_safe_xdg_dir
from .window import BenderWindow

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3


def sanitize_log_message(message: str) -> str:
    """Sanitize a log string by stripping CR/LF and ASCII control characters."""
    cleaned = str(message).replace("\r", " ").replace("\n", " ")
    return _CONTROL_CHARS_RE.sub("", cleaned)


class _SanitizingLogFilter(logging.Filter):
    """Logging filter that strips CR/LF and control characters against log forgery."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitize_log_message(record.getMessage())
        record.args = ()
        return True


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


def setup_logging(state_root: Path | None = None) -> Path | None:
    """
    Configures application-wide logging with owner-only permissions (0700/0600),
    5 MiB size rotation, CR/LF control-character sanitization, and canonical
    XDG path-traversal containment (BEN-12 / CWE-23). If the log path escapes
    its managed directory, file logging is skipped and stdout logging remains.
    """
    # Change Comment (2026-11-21, BEN-12 / Snyk python/PT CWE-23 / CP-ChangeComments):
    # Canonicalize `XDG_STATE_HOME` / `state_root` and enforce `os.path.commonpath`
    # containment before creating directories, opening `bender.log`, or calling `os.chmod`.
    if state_root is not None:
        allowed_base = os.path.realpath(os.fspath(state_root))
        log_dir_real = os.path.realpath(os.path.join(allowed_base, "bender"))
        if not log_dir_real.startswith(allowed_base + os.sep):
            raise ValueError("Invalid logging state_root outside allowed directory")
    else:
        log_dir_real = os.fspath(
            resolve_safe_xdg_dir("XDG_STATE_HOME", ".local/state", "bender")
        )
        allowed_base = os.path.dirname(log_dir_real)

    os.makedirs(log_dir_real, mode=0o700, exist_ok=True)
    try:
        os.chmod(log_dir_real, 0o700)
    except OSError:
        pass

    log_file_real = os.path.realpath(os.path.join(log_dir_real, "bender.log"))
    log_file = None
    if log_file_real.startswith(log_dir_real + os.sep):
        fd = os.open(log_file_real, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.close(fd)
        try:
            os.chmod(log_file_real, 0o600)
        except OSError:
            pass
        log_file = Path(log_file_real)

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        handlers.insert(
            0,
            RotatingFileHandler(
                log_file,
                maxBytes=MAX_LOG_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            ),
        )
    log_filter = _SanitizingLogFilter()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    for handler in handlers:
        handler.addFilter(log_filter)
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = handlers
    logging.info("Bender initialized")
    return log_file


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
