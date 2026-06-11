# Changelog — Bender

All notable changes to the Bender project are documented in this file. This project adheres to Semantic Versioning.

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
