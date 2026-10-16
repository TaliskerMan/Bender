# Changelog — Bender

All notable changes to the Bender project are documented in this file. This project adheres to Semantic Versioning.

> Tagging note: earlier tags mixed `vX.Y.Z` and `vX.Y.Z-N` styles. Going forward,
> use clean SemVer tags (`v0.1.9`) cut from the released commit.

---

## [0.1.13] - 2026-10-16

### Fixed — do no harm
- **Package updates are no longer cut off after 60 seconds.** Every command had
  a 60 s limit, including the time spent at the password prompt, so System
  Update and Flatpak Update could be abandoned part-way while the UI said "timed
  out". Updates now have no time limit.
- **System Update runs non-interactively and keeps your config files.** With no
  terminal, a package asking about a changed config file could stop the upgrade
  half-way. It now answers with dpkg's "keep the installed version" choice. It
  uses nala when installed and falls back to apt-get (it previously failed
  without nala).
- **Clear Shared Memory deleted every file in /dev/shm as root**, including
  files in use by running programs (audio, browsers, databases). It now runs
  without admin rights and deletes only your own files that are over a day old
  and not open or memory-mapped by any program. **Clean Temp Files** follows the
  same rules for `qipc*`/`gdm*` in /tmp.
- **Every Maintenance action asks before it runs** (previously only the GNOME
  reset did), and the output now says whether it finished, failed or was
  cancelled at the password prompt.
- **The blocklist editor can no longer overwrite your list with an error
  message.** If the file can't be read, Save is turned off. Auto-Update (Steven
  Black) now asks whether to merge with or replace your list (it used to
  replace it, dropping domains you added). Saving, Quick Add and Auto-Update
  ask for the password once and apply the change straight away if the proxy is
  running; they no longer start a proxy you had stopped.

### Fixed — claims and results that weren't true
- README said weather came from wttr.in with "no ansiweather required"; it
  comes from `ansiweather` (OpenWeatherMap). README now lists all 8 tabs.
- The Weather tab sent "Austin,TX,USA" to OpenWeatherMap every time Bender
  opened. Nothing is fetched until you click Get Weather; the last location is
  remembered in `~/.config/bender/weather.json` (mode 0600).
- Port Checker used `lsof` (not a dependency), which without admin rights can't
  see other users' programs, so it said "No process listening" for ports held by
  system services. It now uses `ss`, which sees every listening socket.
- Security badges: any output containing "No" showed ✅ (so every November's
  login list "passed"). Each check now judges its own output: ✅ nothing found,
  ⚠️ review, ℹ️ information only, ❌ failed. "Recent User Accounts" (which listed
  all accounts) is now "Accounts with a Login Shell"; the 777 check now finds
  all world-writable files and says it only searches folders you can read.
- Proxy tab: says when tinyproxy's filtering is switched off (the default, in
  which case the blocklist does nothing) and which programs are filtered. "Live"
  log tail renamed; an unreadable log now says so instead of "not found".
- USER_GUIDE.md described features that don't exist (firewall check,
  "ShadowAgent Rules", managing systemd services, removing orphaned packages,
  switching proxy configurations). It now points to the user guide.
- Domain fields accepted values starting with "-", which dig/whois would read as
  an option.
- Connections-per-IP counts split IPv6 addresses at the first colon.

### Changed
- Release: a failed checksum signature now stops the build (it was ignored),
  and the source tarball no longer includes `venv/` or `bin/syft`.
- Package: depends on `iproute2` and `procps`, and on `pkexec` or
  `policykit-1`; no longer depends on `python3-defusedxml` (only a developer
  script uses it).
- Generated Debian build files are no longer tracked in git.
- Lint rules pinned in `pyproject.toml`; tests added for the clean-up rules,
  security badges, tinyproxy config parsing, blocklist merge and port checker.

## [0.1.10–0.1.12]
- Version bumps by the build scripts (docstrings and user documentation added
  in 0.1.10); not individually documented.

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
