# Plan for Bender Release v0.1.15: SonarQube Cloud & ShadowAgent Remediation
- [x] Create `Sonar` branch (`TaliskerMan_Bender`) and gather all 17 SonarQube Cloud and Jira issues.
- [x] Remediate `build_release.sh` and `run.sh` (`5 × shell:S7688`, `4 × shell:S6573`, `0` `shellcheck` warnings).
- [x] Remediate `docs/guide/build_guide.js` and `docs/guide/package.json` (`2 × jssecurity:S8707`, ESM `node:` imports, linear-time $O(n)$ parsers).
- [x] Remediate `tests/test_ui_logic.py` (`3 × python:S9073` composite assertions) and extract pure `tab_about` helpers for headless GTK4 test safety (37/37 tests passing).
- [x] Remediate `.github/workflows/ci.yml`, `requirements.txt`, and `requirements-dev.txt` (`githubactions:S8541`, `githubactions:S8544`, `text:S8565`).
- [x] Harden `src/bender/main.py` with `0700`/`0600` rotated, sanitized diagnostic logging and normalize headers in `data/fix_logo.py` and `replace_app_grid_icon.py`.
- [x] Add `.sonarcloud.properties`, tracked `sonar-project.properties`, `.sonarlint/connectedMode.json`, `.snyk`, and `.dcignore`.
- [x] Regenerate path-sanitized CycloneDX SBOMs (`Audit/SBOM-Linux.json`, `Audit/SBOM-Linux`, `Audit/sbom.json`) and verify 0 vulnerabilities with Grype and Trivy.
- [x] Verify live SonarQube Cloud Quality Gate (`TaliskerMan_Bender` `PASSED`, `0` issues) and merge `Sonar` into `main`.

# Plan for Bender Release v0.1.13

- [x] Merge fix/claims-vs-code to main
- [x] Verify code vs documentation claims (8 tabs, ansiweather, safety gates, no timeouts on updates)
- [x] Add explicit email `chuck@nordheim.online` and version to About tab UI (CP-AboutPage, CP-AutoIncrement)
- [x] Add compliance test for About tab and version display (`test_about_tab_compliance`)
- [x] Modernize `docs/guide/build_guide.js` and eliminate regex backtracking (Sonar S7772, S7785, S8786)
- [x] Refactor `src/bender/cleanup.py` to reduce cognitive complexity below 15 and encapsulate path strings (Sonar S3776, S5443)
- [x] Encapsulate `clean_shm` and `clean_tmp` in `src/bender/tab_maintenance.py` to eliminate S5443 hotspot
- [x] Use string constants in `src/bender/tab_system.py` to eliminate S1192 duplicate literals
- [x] Linearize `parse_tinyproxy_conf` in `src/bender/validators.py` to eliminate regex backtracking (Sonar S8786)
- [x] Run test suite (`pytest` - 36 passed)
- [x] Run polyglot shift-left static analysis and supply chain scanning (`code-gate.sh` - SonarQube, shellcheck, semgrep, osv-scanner, syft, grype all PASS)
- [x] Execute `build_release.sh` to package, GPG sign, SHA512 hash, and stage to `/home/freecode/NOBuilds/Bender-10-16-2026-0.1.13`
- [x] Verify all NOBuilds release artifacts (64-bit DEB, DEB.asc, SHA512, SHA512.asc, checksums.sha512, SHA512SUMS, pubkey.asc, source tarball, LICENSE, README, sbom.json, Bender_User_Guide.pdf)
- [x] Commit release changes, push to GitHub, and create release tag `v0.1.13`

# Plan for Bender Release v0.1.14: High-Resolution Icon Fix
- [x] Restore pristine 512×512 master application icon (`data/icons/hicolor/512x512/apps/com.taliskerman.bender.png`).
- [x] Generate full hicolor icon resolution suite (`16x16` through `512x512`) using Lanczos resampling.
- [x] Update `debian/install` to distribute all 9 resolution tiers across `/usr/share/icons/hicolor/`.
- [x] Auto-increment version to `0.1.14` across `pyproject.toml`, `src/bender/__init__.py`, `debian/changelog`, `CHANGELOG.md`, `docs/guide/Bender_User_Guide.md`.
- [x] Run static analysis (Semgrep) and vulnerability scanning (Grype, OSV-Scanner).
- [x] Execute `build_release.sh` to package Debian package, detached GPG sign, and stage to `/home/freecode/NOBuilds/Bender-10-23-2026-0.1.14`.
- [x] Commit changes, tag `v0.1.14`, push to GitHub, and publish official release with all assets.
