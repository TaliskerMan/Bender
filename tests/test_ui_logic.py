# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender. Released under the GNU GPL v3.

"""Behaviour of the GTK tabs that doesn't need a display. Skipped where the
GTK 4 / Libadwaita Python bindings aren't installed (e.g. plain CI)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk  # noqa: F401
except (ImportError, ValueError):
    pytest.skip("GTK 4 / Libadwaita bindings not installed", allow_module_level=True)

from bender import runner, tab_maintenance, tab_network, tab_weather  # noqa: E402


def test_every_maintenance_action_asks_first():
    for action in tab_maintenance.ACTIONS:
        assert action.get("confirm"), action["label"]


def test_updates_have_no_time_limit():
    # A 60 s limit used to cut package upgrades off part-way.
    for action in tab_maintenance.ACTIONS:
        if "Update" in action["label"]:
            assert action["timeout"] is None, action["label"]


def test_system_update_is_non_interactive_and_keeps_configs():
    script = tab_maintenance.SYSTEM_UPDATE_SCRIPT
    assert "DEBIAN_FRONTEND=noninteractive" in script
    assert "--force-confold" in script and "--force-confdef" in script
    assert "nala" in script and "apt-get" in script


def test_shared_memory_clean_up_runs_without_root():
    shm = next(a for a in tab_maintenance.ACTIONS if "/dev/shm" in a["label"])
    assert shm["kind"] == "python"


def test_result_text_shows_failures():
    text = tab_maintenance.format_result("", "Error executing command as another "
                                         "user: Request dismissed", 126, privileged=True)
    assert "dismissed" in text and text.endswith("prompt was dismissed.")
    assert tab_maintenance.format_result("done", "", 0).endswith("Finished.")
    assert "exit code 2" in tab_maintenance.format_result("partial", "boom", 2)


def test_runner_timeout_and_stdin(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)

        class R:
            stdout = stderr = ""
            returncode = 0
        return R()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner.GLib, "idle_add", lambda *a: None)
    monkeypatch.setattr(runner.threading, "Thread",
                        lambda target, daemon: type("T", (), {"start": lambda s: target()})())
    runner.CommandRunner.run(["true"], lambda *a: None, timeout=None)
    assert captured["timeout"] is None
    assert captured["stdin"] is runner.subprocess.DEVNULL


def test_port_checker_text():
    assert tab_network.describe_port("22", "", "", 0) == "Nothing is listening on TCP port 22."
    shown = tab_network.describe_port("22", "LISTEN 0 128 0.0.0.0:22 0.0.0.0:*", "", 0)
    assert "another user" in shown
    own = tab_network.describe_port(
        "8000", 'LISTEN 0 5 127.0.0.1:8000 0.0.0.0:* users:(("python3",pid=1,fd=3))', "", 0)
    assert "another user" not in own


def test_weather_location_is_remembered_privately(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert tab_weather.load_weather_settings() == {"location": "", "metric": False}
    tab_weather.save_weather_settings("Austin,TX,USA", True)
    assert tab_weather.load_weather_settings() == {"location": "Austin,TX,USA", "metric": True}
    mode = os.stat(tmp_path / "bender" / "weather.json").st_mode & 0o777
    assert mode == 0o600


def test_about_tab_compliance():
    """Verify About tab contains copyright Chuck Talk, email, and version per CP-AboutPage and CP-AutoIncrement."""
    from bender import tab_about, __version__
    about = tab_about.AboutTab()
    labels = []

    def collect_labels(widget):
        if isinstance(widget, Gtk.Label):
            labels.append(widget.get_label())
        child = widget.get_first_child()
        while child:
            collect_labels(child)
            child = child.get_next_sibling()

    collect_labels(about)
    label_text = " ".join(labels)
    assert "Chuck Talk" in label_text
    assert "chuck@nordheim.online" in label_text
    assert __version__ in label_text
