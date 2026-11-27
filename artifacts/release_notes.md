# Bender v0.1.17 Official Linux Release

Bender is a GTK4 + Libadwaita workstation dashboard for the Linux desktop (GNOME, Pop!_OS, Debian/Ubuntu) providing system health monitoring, read-only security checks, network & socket inspection, confirmation-gated maintenance utilities, OpenWeatherMap (`ansiweather`) forecasting, and Tinyproxy ad-blocking management.

## What's Changed Since v0.1.14 (`v0.1.15` – `v0.1.17`)
- **Snyk Code Path Traversal Hardening (`BEN-12`, `CWE-23`):** Added canonical XDG Base Directory containment (`resolve_safe_xdg_dir`) and symlink guards across `setup_logging()` (`~/.local/state/bender/bender.log`) and Weather settings (`~/.config/bender/weather.json`), achieving **`0` Snyk Code & Open Source issues**.
- **SonarQube Cloud Full Clean-Code & Security Pass (`TaliskerMan_Bender`):** Resolved all 17 SonarQube Cloud issues across Python, Node ESM (`docs/guide/build_guide.js`), Bash (`build_release.sh`, `run.sh`), and SHA-pinned GitHub Actions CI, achieving **Quality Gate `OK` (`A/A/A/A` ratings, `0` Bugs, `0` Vulnerabilities, `0` Code Smells, `0` Security Hotspots)**.
- **Owner-Only Rotated Diagnostic Logging (`CP-Logging`):** Enforced `0700` directory and `0600` file permissions on `~/.local/state/bender/bender.log` with 5 MiB `RotatingFileHandler` rotation and CR/LF log-injection sanitization (`42 / 42` unit & AST invariant tests passing).
- **Refreshed User Guide & Clean Source Tarball (`v0.1.17`):** Updated `README.md`, `Bender_User_Guide.md`, and `Bender_User_Guide.pdf` with `v0.1.17` verification commands and XDG log documentation, regenerated CycloneDX SBOMs (`0` Grype/Trivy/OSV vulnerabilities), and excluded local scanner/linter caches from `bender_source.tar.gz`.

## Package Integrity & Verification

| Asset | Description |
|---|---|
| `bender_0.1.17_all.deb` | Debian/Ubuntu architecture-independent 64-bit desktop package |
| `bender_0.1.17_all.deb.asc` | GPG ASCII-armored detached signature |
| `bender_0.1.17_all.deb.sig` | GPG binary detached signature |
| `bender_0.1.17_all.deb.sha512` | SHA-512 checksum |
| `bender_0.1.17_all.deb.sha512.asc` | Clearsigned SHA-512 checksum |
| `bender_0.1.17_all.deb.sha256` | SHA-256 checksum |
| `pubkey.asc` / `chuck_pubkey.asc` | Maintainer GPG public key (`Chuck Talk <chuck@nordheim.online>`) |
| `bender_source.tar.gz` | Corresponding GPLv3 source archive |
| `SBOM-Linux.json` / `sbom.json` | CycloneDX SBOM (Software Bill of Materials) |
| `security_report.md` | Multi-scanner security and quality audit report |
| `Bender_User_Guide.pdf` | Official User Guide & manual (`v0.1.17`) |
| `SHA512SUMS` / `SHA256SUMS` | Combined release asset checksum manifests |

### Verification Instructions

Import the release signing key and verify the Debian package:
```bash
# Import Chuck Talk's release signing key
gpg --import chuck_pubkey.asc

# Verify the GPG detached signature
gpg --verify bender_0.1.17_all.deb.asc bender_0.1.17_all.deb

# Verify SHA-512 checksum
sha512sum -c bender_0.1.17_all.deb.sha512
```

### Installation
```bash
sudo apt install ./bender_0.1.17_all.deb
```
