# Changelog — Bender

All notable changes to the Bender project are documented in this file. This project adheres to Semantic Versioning.

> Tagging note: earlier tags mixed `vX.Y.Z` and `vX.Y.Z-N` styles. Going forward,
> use clean SemVer tags (`v0.1.9`) cut from the released commit.

---

## [0.1.9] - 2026-06-22

### Fixed
- **Four privileged actions no longer crash.** Start Proxy, Stop Proxy, Hidden
  Processes (unhide), and DNS Flush called `run_shell(..., use_sudo=True)`, which
  raises `ValueError`. They now use list-form `CommandRunner.run([...],
  use_sudo=True)`; shell-only fallbacks (the unhide `|| echo`, the DNS `&& echo`)
  moved into Python callbacks.

### Added
- **Tests + enforced invariants.** A `pytest` suite covering the input validators
  and the Steven Black hosts parser, plus AST-based tests that fail the build if
  any `run_shell` call passes `use_sudo=True` or builds its command string with an
  f-string/concatenation/`.format()`.

### Changed
- **Licensing normalized to GPLv3** and contact to `chuck@nordheim.online` across
  all source headers, `SECURITY.md`, and the About tab (previously 9 files said
  AGPLv3 / used the gmail address).
- **Dependencies/packaging:** removed the unused `defusedxml`; declared the
  optional runtime tools (`dnsutils`, `whois`, `unhide`, `flatpak`, `tinyproxy`,
  `ansiweather`) in `Recommends` and `nala` in `Suggests`.
- **Versioning single-sourced** to `pyproject.toml`; `build_release.sh` no longer
  references a hardcoded author path and verifies the Debian version matches.

## [0.1.5–0.1.8]
- Interim packaging/build iterations (logo and legal fixes, version bumps). These
  were built but not individually documented; folded into the 0.1.9 reconciliation.

---

## [0.1.4] - 2026-05-28

### Added
- **Build Helper script Integration:** Added auto-increment version automation to increment patch releases during packaging.
- **Debian Changelog Sync:** Aligned package controls with the system version file.

---

## [0.1.3] - 2026-04-21

### Changed
- **Secure Process Execution:** Replaced string command interpolation in subprocess actions with list-form arguments to close command injection vectors across all tabs.
- **XML Parsing Hardening:** Migrated from Python's standard XML parser modules to `defusedxml` to block XML External Entity (XXE) vulnerabilities.
- **Timeout and Size Limits:** Enforced download bounds and response timeouts on remote operations to protect network brokers.

---

## [0.1.2] - 2026-04-05

### Added
- **UI Modernisation:** Refactored GNOME Master Terminal into a unified layout for Maintenance and Security dashboards.
- **UI Refinements:** Extracted the Connections component, repaired GTK widget scaling, and replaced the Weather forecasting unit selector.

### Changed
- **Argument Injection Protections:** Sealed arguments validation holes targeting data retrieve endpoints.

---

## [0.1.1] - 2026-03-27

### Added
- **Application Logger:** Added centralized log tracking to record application status and background command logs.
- **subprocess Sanitization:** Removed unsafe `shell=True` configurations across Network and Proxy tabs.

---

## [0.1.0] - 2026-03-02

### Added
- **Initial Release:** Polished GTK4 + libadwaita workstation administration GUI dashboard with 6 views:
  - System Overview
  - Security Audit
  - Network Monitor
  - Maintenance
  - Weather
  - Proxy Manager
