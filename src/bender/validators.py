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
# metacharacters, spaces, or slashes can pass.
_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+$")
_CITY_RE = re.compile(r"^[a-zA-Z0-9.,_ ]+$")


def is_valid_domain(value: str) -> bool:
    """True if [value] is a syntactically safe domain (no injection chars)."""
    return bool(value) and _DOMAIN_RE.match(value) is not None


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
