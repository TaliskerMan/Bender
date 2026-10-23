#!/bin/bash
# build_release.sh — Automated build, sign, and hash script for Bender
#
# SINGLE SOURCE OF TRUTH: pyproject.toml `version` is the upstream version.
# debian/changelog must carry the same upstream version with a `-N` Debian
# revision (e.g. pyproject 0.1.14 -> debian 0.1.14). This script reads the
# Debian version from debian/changelog and verifies it matches pyproject.
set -e

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
PACKAGE_NAME="bender"
VERSION=$(head -1 debian/changelog | grep -oP '(?<=^bender \().*?(?=\))')
PYPROJECT_VERSION=$(grep -oP '(?<=^version = ")[^"]+' pyproject.toml)
if [ "${VERSION%%-*}" != "$PYPROJECT_VERSION" ]; then
    echo "ERROR: version mismatch — debian/changelog=${VERSION} vs pyproject=${PYPROJECT_VERSION}." >&2
    echo "Update them to agree (pyproject is the source of truth) before building." >&2
    exit 1
fi
GPG_EMAIL="chuck@nordheim.online"
BUILD_DIR="artifacts"

echo "=================================================="
echo "🤖 Building Bender v${VERSION}"
echo "=================================================="

# Ensure artifacts directory exists
mkdir -p "$BUILD_DIR"

# Clean old artifacts
rm -rf ${BUILD_DIR}/*

echo "==> Generating SBOM via Syft..."
SYFT_BIN="syft"
if ! command -v syft &> /dev/null; then
    if [ -f "${HOME}/.local/bin/syft" ]; then
        SYFT_BIN="${HOME}/.local/bin/syft"
    elif [ -f "./syft" ]; then
        SYFT_BIN="./syft"
    fi
fi
if command -v "${SYFT_BIN}" &> /dev/null; then
    mkdir -p Audit
    "${SYFT_BIN}" dir:. \
        --exclude ./venv \
        --exclude ./.venv \
        --exclude ./android \
        --exclude ./ios \
        --exclude ./macos \
        --exclude ./build \
        --exclude ./packaging_output \
        --exclude ./dist \
        --exclude ./plan \
        --exclude ./artifacts \
        --exclude ./Audit \
        --exclude "./*.deb" \
        --exclude "./*.tar.gz" \
        -o cyclonedx-json > Audit/SBOM-Linux.json
    cp Audit/SBOM-Linux.json Audit/SBOM-Linux
    cp Audit/SBOM-Linux.json Audit/sbom.json
fi

# Build the package natively
echo "[1/4] Building Debian package..."
dpkg-buildpackage -us -uc -b

# Move artifacts to the build folder
mv ../${PACKAGE_NAME}_${VERSION}*.deb "$BUILD_DIR/"
mv ../${PACKAGE_NAME}_${VERSION}*.changes "$BUILD_DIR/" 2>/dev/null || true
mv ../${PACKAGE_NAME}_${VERSION}*.buildinfo "$BUILD_DIR/" 2>/dev/null || true

DEB_FILE="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"

# Generate detached GPG signatures per L-DEB-Packaging & L-Release
echo "[2/4] Generating GPG detached signatures for .deb..."
gpg --batch --yes --armor --pinentry-mode loopback --detach-sign --default-key "$GPG_EMAIL" "$DEB_FILE"
gpg --batch --yes --pinentry-mode loopback --detach-sign --output "${DEB_FILE}.sig" --default-key "$GPG_EMAIL" "$DEB_FILE"

# Export public keys
gpg --batch --yes --armor --export "$GPG_EMAIL" > "${BUILD_DIR}/pubkey.asc"
cp "${BUILD_DIR}/pubkey.asc" "${BUILD_DIR}/chuck_pubkey.asc"

# Generate SHA512 and SHA256 hashsums
echo "[3/4] Generating hashsums..."
sha512sum "$DEB_FILE" > "${DEB_FILE}.sha512"
sha256sum "$DEB_FILE" > "${DEB_FILE}.sha256"
gpg --batch --yes --clearsign --pinentry-mode loopback --default-key "$GPG_EMAIL" "${DEB_FILE}.sha512"

# Copy to NOBuilds directory
echo "[4/4] Copying to NOBuilds directory..."
DATE_STR=$(date +%m-%d-%Y)
NOBUILDS_DIR="${HOME}/NOBuilds/Bender-${DATE_STR}-${VERSION}"
mkdir -p "${NOBUILDS_DIR}"

# Generate source code archive
echo "Generating source tarball..."
tar --exclude=debian --exclude=.git --exclude=artifacts --exclude=__pycache__ \
    --exclude=build --exclude=.pybuild --exclude=./venv --exclude=./.venv \
    --exclude=./bin --exclude='*.tar.gz' --exclude=.pytest_cache --exclude=.DS_Store \
    --exclude=Audit \
    -czf "${NOBUILDS_DIR}/bender_source.tar.gz" .
cp "${NOBUILDS_DIR}/bender_source.tar.gz" "${BUILD_DIR}/"

# Copy packages and signatures
cp "$DEB_FILE" "${NOBUILDS_DIR}/"
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
cp Audit/SBOM-Linux.json "${NOBUILDS_DIR}/" || true
cp Audit/SBOM-Linux "${NOBUILDS_DIR}/" || true
cp Audit/sbom.json "${NOBUILDS_DIR}/" || true
if [ -f "Audit/security_report.md" ]; then
    cp Audit/security_report.md "${BUILD_DIR}/"
    cp Audit/security_report.md "${NOBUILDS_DIR}/"
fi
if [ -f "docs/Bender_User_Guide.pdf" ]; then
    cp docs/Bender_User_Guide.pdf "${BUILD_DIR}/"
    cp docs/Bender_User_Guide.pdf "${NOBUILDS_DIR}/"
fi

( cd "${BUILD_DIR}" && rm -f SHA512SUMS SHA256SUMS && sha512sum * > SHA512SUMS 2>/dev/null || true && sha256sum * > SHA256SUMS 2>/dev/null || true )
( cd "${NOBUILDS_DIR}" && rm -f SHA512SUMS SHA256SUMS && sha512sum * > SHA512SUMS 2>/dev/null || true && sha256sum * > SHA256SUMS 2>/dev/null || true )

echo "=================================================="
echo "✅ Build Complete!"
echo "Package: $DEB_FILE"
echo "Hashsum: ${DEB_FILE}.sha512"
echo "Local:   $NOBUILDS_DIR"
