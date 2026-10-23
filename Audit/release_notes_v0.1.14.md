# Bender v0.1.14 Official Linux Release

Bender is a workstation dashboard for the Linux desktop (GNOME, Cosmic) providing system health monitoring, network inspection, maintenance utilities, weather tracking, and Tinyproxy management in an Adwaita interface.

## What's Changed in v0.1.14
- **High-Resolution Master Icon Restored:** Restored the uncompressed 512×512 master application icon (`data/icons/hicolor/512x512/apps/com.taliskerman.bender.png`), resolving blurry, low-resolution rendering on GNOME Dash, AppGrid, and desktop launchers.
- **Complete Hicolor Icon Resolution Suite:** Generated and packaged all standard desktop icon sizes (`16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `96x96`, `128x128`, `256x256`, and `512x512`) using high-quality Lanczos resampling.
- **Packaging & Installation Enhancement:** Updated Debian packaging (`debian/install`) to distribute the complete resolution suite to `/usr/share/icons/hicolor/`.
- **Security Audit & Signatures:** Clean passes across Semgrep SAST and Syft/Grype vulnerability analysis; official Debian distribution cryptographically signed with Chuck Talk's GPG maintainer key (`chuck@nordheim.online`).

## Package Integrity & Verification

| Asset | Description |
|---|---|
| `bender_0.1.14_all.deb` | Debian/Ubuntu architecture-independent package |
| `bender_0.1.14_all.deb.asc` | GPG ASCII-armored detached signature |
| `bender_0.1.14_all.deb.sig` | GPG binary detached signature |
| `bender_0.1.14_all.deb.sha512` | SHA-512 checksum |
| `bender_0.1.14_all.deb.sha256` | SHA-256 checksum |
| `pubkey.asc` / `chuck_pubkey.asc` | Maintainer GPG public key (`chuck@nordheim.online`) |
| `SBOM-Linux.json` / `sbom.json` | CycloneDX SBOM (Software Bill of Materials) |
| `security_report.md` | Security and vulnerability scan report |
| `Bender_User_Guide.pdf` | Official User Guide & manual |

### Verification Instructions

Import the release signing key and verify the Debian package:
```bash
# Import Chuck Talk's release signing key
gpg --import chuck_pubkey.asc

# Verify the GPG detached signature
gpg --verify bender_0.1.14_all.deb.asc bender_0.1.14_all.deb

# Verify SHA-512 checksum
sha512sum -c bender_0.1.14_all.deb.sha512
```

### Installation
```bash
sudo apt install ./bender_0.1.14_all.deb
```
