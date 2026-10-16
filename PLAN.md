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
- [ ] Commit release changes, push to GitHub, and create release tag `v0.1.13`
