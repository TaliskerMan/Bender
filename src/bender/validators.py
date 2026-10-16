# Copyright (C) 2026 Chuck Talk <chuck@nordheim.online>
# This file is part of Bender.
#
# Bender is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# Bender is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY. See the GNU GPL v3 for details.

"""Pure input-validation and parsing helpers.

These exist so the security-sensitive validation (which keeps user input out of
command construction) and the Steven Black hosts parser can be unit-tested
without a GTK display.
"""

import re

# A conservative allowlist: letters, digits, dots and hyphens only — no shell
# metacharacters, spaces, or slashes can pass. The first character must be a
# letter or digit: a value starting with "-" would be read by dig/whois as an
# option rather than a domain.
_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*$")
_MAX_DOMAIN_LENGTH = 253
_CITY_RE = re.compile(r"^[a-zA-Z0-9.,_ ]+$")


def is_valid_domain(value: str) -> bool:
    """True if [value] is a syntactically safe domain (no injection chars)."""
    return (
        bool(value)
        and len(value) <= _MAX_DOMAIN_LENGTH
        and _DOMAIN_RE.match(value) is not None
    )


def is_valid_city(value: str) -> bool:
    """True if [value] is a safe city/location string for the weather lookup."""
    return bool(value) and _CITY_RE.match(value) is not None


def parse_hosts_blocklist(raw: str) -> list:
    """Parse a Steven Black-style hosts file into a list of blocked domains.

    Keeps only ``0.0.0.0 <domain>`` entries whose domain is valid, skipping
    comments, malformed lines, and the localhost aliases.
    """
    domains = []
    for line in raw.splitlines():
        parts = line.split()
        if (
            line.startswith("0.0.0.0")
            and len(parts) >= 2
            and parts[1] not in ("0.0.0.0", "localhost", "localhost.localdomain")
            and is_valid_domain(parts[1])
        ):
            domains.append(parts[1])
    return domains


# tinyproxy's default config file (Debian/Ubuntu package).
TINYPROXY_CONF = "/etc/tinyproxy/tinyproxy.conf"

def parse_tinyproxy_conf(text: str) -> dict:
    """Read the settings Bender needs from tinyproxy.conf.

    Returns {"filter": <filter file path or None>, "port": <int or None>}.
    "filter" is None when no active (uncommented) ``Filter`` line exists, which
    is how tinyproxy ships: with it, the blocklist is ignored entirely.
    """
    settings = {"filter": None, "port": None}
    for raw_line in text.splitlines():
        # Strip trailing comments and surrounding whitespace per CP-Comments (linear parse, no ReDoS)
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        key = parts[0].lower()
        value = parts[1].strip().strip('"').strip("'").strip()
        if key == "filter" and value:
            settings["filter"] = value
        elif key == "port" and value.isdigit():
            settings["port"] = int(value)
    return settings


def merge_blocklists(existing: str, downloaded: list) -> str:
    """Keep every line of the user's *existing* blocklist and append the
    *downloaded* domains it doesn't already contain."""
    lines = existing.splitlines()
    present = {line.strip() for line in lines}
    added = [domain for domain in downloaded if domain not in present]
    merged = lines + added
    return "\n".join(merged) + "\n" if merged else ""
