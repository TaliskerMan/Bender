# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender. Released under the GNU GPL v3.

"""Unit tests for the input validators and the Steven Black hosts parser."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bender.validators import (  # noqa: E402
    is_valid_domain,
    is_valid_city,
    merge_blocklists,
    parse_hosts_blocklist,
    parse_tinyproxy_conf,
)


class TestIsValidDomain:
    def test_accepts_plain_domains(self):
        assert is_valid_domain("example.com")
        assert is_valid_domain("sub.example.co.uk")
        assert is_valid_domain("my-host123.net")

    def test_rejects_injection_and_whitespace(self):
        for bad in [
            "",
            "example.com; rm -rf /",
            "example.com && reboot",
            "$(whoami).com",
            "a b.com",
            "example.com/../etc",
            "exa|mple.com",
            "`id`.com",
        ]:
            assert not is_valid_domain(bad), bad

    def test_rejects_values_that_look_like_options(self):
        # dig/whois would read these as options, not domains.
        for bad in ["-h", "-x", "--help", ".example.com", "a" * 254]:
            assert not is_valid_domain(bad), bad


class TestIsValidCity:
    def test_accepts_city_names(self):
        assert is_valid_city("New York")
        assert is_valid_city("São".encode("ascii", "ignore").decode() or "Paris")
        assert is_valid_city("Washington, DC")

    def test_rejects_shell_metacharacters(self):
        assert not is_valid_city("London; rm -rf /")
        assert not is_valid_city("$(reboot)")
        assert not is_valid_city("")


class TestParseHostsBlocklist:
    def test_keeps_only_blocked_domains(self):
        raw = (
            "# Title: StevenBlack/hosts\n"
            "#\n"
            "127.0.0.1 localhost\n"
            "0.0.0.0 0.0.0.0\n"
            "0.0.0.0 localhost\n"
            "0.0.0.0 ads.example.com\n"
            "0.0.0.0 tracker.evil.net\n"
            "0.0.0.0\n"  # malformed (no domain)
            "0.0.0.0 bad domain.com\n"  # 3 fields; parts[1]='bad' is valid though
            "\n"
        )
        domains = parse_hosts_blocklist(raw)
        assert "ads.example.com" in domains
        assert "tracker.evil.net" in domains
        assert "localhost" not in domains
        assert "0.0.0.0" not in domains

    def test_ignores_comment_and_non_block_lines(self):
        raw = "# comment\n127.0.0.1 example.com\nnonsense line\n"
        assert parse_hosts_blocklist(raw) == []

    def test_rejects_domains_with_injection_chars(self):
        raw = "0.0.0.0 evil.com;rm\n0.0.0.0 good.com\n"
        domains = parse_hosts_blocklist(raw)
        assert "good.com" in domains
        assert all(";" not in d for d in domains)


class TestTinyproxyConf:
    def test_shipped_config_has_filter_off(self):
        conf = (
            'User tinyproxy\nPort 8888\n'
            '# Filter: This allows you to specify the location of the filter file.\n'
            '#Filter "/etc/tinyproxy/filter"\n'
        )
        assert parse_tinyproxy_conf(conf) == {"filter": None, "port": 8888}

    def test_active_filter_line(self):
        conf = 'Port 3128\nFilter "/etc/tinyproxy/blocked"  # mine\n'
        assert parse_tinyproxy_conf(conf) == {"filter": "/etc/tinyproxy/blocked", "port": 3128}

    def test_unquoted_filter(self):
        assert parse_tinyproxy_conf("  Filter /etc/tinyproxy/filter\n")["filter"] == "/etc/tinyproxy/filter"


class TestMergeBlocklists:
    def test_keeps_user_entries_and_adds_new(self):
        merged = merge_blocklists("# mine\nmysite.com\nads.example.com\n",
                                  ["ads.example.com", "tracker.net"])
        assert merged == "# mine\nmysite.com\nads.example.com\ntracker.net\n"

    def test_empty_existing(self):
        assert merge_blocklists("", ["a.com"]) == "a.com\n"
