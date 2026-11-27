#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Author: Chuck Talk, <chuck@nordheim.online>
# Project: Bender
# Purpose: Automated build, GPG sign, SHA-512/SHA-256 hash, and SBOM script.
# Updated: 2026-11-27 (CP-ChangeComments: exclude local linter/scanner caches from source tarball)
###############################################################################
# SINGLE SOURCE OF TRUTH: pyproject.toml `version` is the upstream version.
# debian/changelog must carry the same upstream version with an optional `-N`
# Debian revision (e.g. pyproject 0.1.15 -> debian 0.1.15). This script reads
# the Debian version from debian/changelog and verifies it matches pyproject.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
cd "${SCRIPT_DIR}"

readonly PACKAGE_NAME="bender"
readonly GPG_EMAIL="chuck@nordheim.online"
readonly BUILD_DIR="artifacts"
readonly AUDIT_DIR="Audit"
readonly PRIMARY_SBOM="${AUDIT_DIR}/SBOM-Linux.json"
readonly SEPARATOR="=================================================="

VERSION="$(head -n 1 debian/changelog | grep -oP '(?<=^bender \().*?(?=\))')"
readonly VERSION
PYPROJECT_VERSION="$(grep -oP '(?<=^version = ")[^"]+' pyproject.toml)"
readonly PYPROJECT_VERSION

if [[ "${VERSION%%-*}" != "${PYPROJECT_VERSION}" ]]; then
    echo "ERROR: version mismatch — debian/changelog=${VERSION} vs pyproject=${PYPROJECT_VERSION}." >&2
    echo "Update them to agree (pyproject is the source of truth) before building." >&2
    exit 1
fi

echo "${SEPARATOR}"
echo "🤖 Building Bender v${VERSION}"
echo "${SEPARATOR}"

# Ensure artifacts directory exists and clean old build artifacts safely
mkdir -p "${BUILD_DIR}"
find "${BUILD_DIR}" -mindepth 1 -maxdepth 1 ! -name '.keep' ! -name 'chuck_pubkey.asc' ! -name 'release_notes.md' -exec rm -rf -- {} + 2>/dev/null || true

echo "==> Generating SBOM via Syft..."
SYFT_BIN="syft"
if ! command -v syft >/dev/null 2>&1; then
    if [[ -f "${HOME}/.local/bin/syft" ]]; then
        SYFT_BIN="${HOME}/.local/bin/syft"
    elif [[ -f "./syft" ]]; then
        SYFT_BIN="./syft"
    fi
fi

if command -v "${SYFT_BIN}" >/dev/null 2>&1; then
    mkdir -p "${AUDIT_DIR}"
    "${SYFT_BIN}" scan dir:. \
        --source-name "${PACKAGE_NAME}" \
        --source-version "${VERSION}" \
        --exclude './venv/**' \
        --exclude './.venv/**' \
        --exclude './bin/**' \
        --exclude './build/**' \
        --exclude './.pybuild/**' \
        --exclude './debian/bender/**' \
        --exclude './packaging_output/**' \
        --exclude './dist/**' \
        --exclude './plan/**' \
        --exclude './preso/**' \
        --exclude './artifacts/**' \
        --exclude './Audit/**' \
        --exclude './*.deb' \
        --exclude './*.tar.gz' \
        -o "cyclonedx-json=${PRIMARY_SBOM}"
    sed -i "s|${SCRIPT_DIR}/\?||g" "${PRIMARY_SBOM}"
    cp "${PRIMARY_SBOM}" "${AUDIT_DIR}/SBOM-Linux"
    cp "${PRIMARY_SBOM}" "${AUDIT_DIR}/sbom.json"
fi

# Build the package natively
echo "[1/4] Building Debian package..."
dpkg-buildpackage -us -uc -b

# Move artifacts to the build folder (shell:S6573 safe path prefixes)
mv -- ../"${PACKAGE_NAME}_${VERSION}"*.deb "${BUILD_DIR}/"
mv -- ../"${PACKAGE_NAME}_${VERSION}"*.changes "${BUILD_DIR}/" 2>/dev/null || true
mv -- ../"${PACKAGE_NAME}_${VERSION}"*.buildinfo "${BUILD_DIR}/" 2>/dev/null || true

readonly DEB_BASENAME="${PACKAGE_NAME}_${VERSION}_all.deb"
readonly DEB_FILE="${BUILD_DIR}/${DEB_BASENAME}"

# Generate detached GPG signatures per L-DEB-Packaging & L-Release
echo "[2/4] Generating GPG detached signatures for .deb..."
gpg --batch --yes --armor --pinentry-mode loopback --detach-sign --default-key "${GPG_EMAIL}" "${DEB_FILE}"
gpg --batch --yes --pinentry-mode loopback --detach-sign --output "${DEB_FILE}.sig" --default-key "${GPG_EMAIL}" "${DEB_FILE}"

# Export public keys
gpg --batch --yes --armor --export "${GPG_EMAIL}" > "${BUILD_DIR}/pubkey.asc"
cp "${BUILD_DIR}/pubkey.asc" "${BUILD_DIR}/chuck_pubkey.asc"

# Generate SHA512 and SHA256 hashsums using basename so sha512sum -c works in Downloads/NOBuilds
echo "[3/4] Generating hashsums..."
(
    cd "${BUILD_DIR}"
    sha512sum -- "${DEB_BASENAME}" > "${DEB_BASENAME}.sha512"
    sha256sum -- "${DEB_BASENAME}" > "${DEB_BASENAME}.sha256"
)
gpg --batch --yes --clearsign --pinentry-mode loopback --default-key "${GPG_EMAIL}" "${DEB_FILE}.sha512"

# Copy to NOBuilds directory
echo "[4/4] Copying to NOBuilds directory..."
DATE_STR="$(date +%m-%d-%Y)"
readonly DATE_STR
readonly NOBUILDS_DIR="${HOME}/NOBuilds/Bender-${DATE_STR}-${VERSION}"
mkdir -p "${NOBUILDS_DIR}"

# Generate source code archive
echo "Generating source tarball..."
tar --exclude=debian --exclude=.git --exclude=artifacts --exclude=__pycache__ \
    --exclude=build --exclude=.pybuild --exclude=./venv --exclude=./.venv \
    --exclude=./bin --exclude='*.tar.gz' --exclude=.pytest_cache --exclude=.ruff_cache \
    --exclude=.scannerwork --exclude=.circleci --exclude=.sonarlint --exclude='**/node_modules' \
    --exclude=.DS_Store --exclude=Audit --exclude=preso \
    -czf "${NOBUILDS_DIR}/bender_source.tar.gz" .
cp "${NOBUILDS_DIR}/bender_source.tar.gz" "${BUILD_DIR}/"

# Copy packages and signatures
cp "${DEB_FILE}" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.asc" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.sig" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.sha512" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.sha512.asc" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.sha256" "${NOBUILDS_DIR}/"
cp "${BUILD_DIR}/pubkey.asc" "${NOBUILDS_DIR}/"
cp "${BUILD_DIR}/chuck_pubkey.asc" "${NOBUILDS_DIR}/"

# Copy license, readme, sbom, and user guide PDF per L-Release
cp LICENSE "${NOBUILDS_DIR}/"
cp README.md "${NOBUILDS_DIR}/"
cp "${PRIMARY_SBOM}" "${NOBUILDS_DIR}/" || true
cp "${AUDIT_DIR}/SBOM-Linux" "${NOBUILDS_DIR}/" || true
cp "${AUDIT_DIR}/sbom.json" "${NOBUILDS_DIR}/" || true

if [[ -f "${AUDIT_DIR}/security_report.md" ]]; then
    cp "${AUDIT_DIR}/security_report.md" "${BUILD_DIR}/"
    cp "${AUDIT_DIR}/security_report.md" "${NOBUILDS_DIR}/"
fi

if [[ -f "docs/Bender_User_Guide.pdf" ]]; then
    cp "docs/Bender_User_Guide.pdf" "${BUILD_DIR}/"
    cp "docs/Bender_User_Guide.pdf" "${NOBUILDS_DIR}/"
fi

(
    cd "${BUILD_DIR}"
    rm -f -- SHA512SUMS SHA256SUMS
    sha512sum -- ./* > SHA512SUMS 2>/dev/null || true
    sha256sum -- ./* > SHA256SUMS 2>/dev/null || true
)
(
    cd "${NOBUILDS_DIR}"
    rm -f -- SHA512SUMS SHA256SUMS
    sha512sum -- ./* > SHA512SUMS 2>/dev/null || true
    sha256sum -- ./* > SHA256SUMS 2>/dev/null || true
)

echo "${SEPARATOR}"
echo "✅ Build Complete!"
echo "Package: ${DEB_FILE}"
echo "Hashsum: ${DEB_FILE}.sha512"
echo "Local:   ${NOBUILDS_DIR}"
