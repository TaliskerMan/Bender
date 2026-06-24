#!/bin/bash
# build_release.sh — Automated build, sign, and hash script for Bender
#
# SINGLE SOURCE OF TRUTH: pyproject.toml `version` is the upstream version.
# debian/changelog must carry the same upstream version with a `-N` Debian
# revision (e.g. pyproject 0.1.9 -> debian 0.1.9-1). This script reads the
# Debian version from debian/changelog and verifies it matches pyproject; it no
# longer calls an author-specific increment script.
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
rm -f ${BUILD_DIR}/${PACKAGE_NAME}*

# Build the package natively
echo "[1/4] Building Debian package..."
dpkg-buildpackage -us -uc -b

# Move artifacts to the build folder
mv ../${PACKAGE_NAME}_${VERSION}*.deb "$BUILD_DIR/"
mv ../${PACKAGE_NAME}_${VERSION}*.changes "$BUILD_DIR/" 2>/dev/null || true
mv ../${PACKAGE_NAME}_${VERSION}*.buildinfo "$BUILD_DIR/" 2>/dev/null || true

DEB_FILE="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"

# Generate detached GPG signatures (standard for GitHub releases since dpkg-sig is deprecated)
echo "[2/4] Generating GPG detached signature for .deb..."
gpg --armor --detach-sign --default-key "$GPG_EMAIL" "$DEB_FILE"

# Generate SHA512 hashsum and sign it
echo "[3/4] Generating SHA512 hashsum..."
cd "$BUILD_DIR"
sha512sum "${PACKAGE_NAME}_${VERSION}_all.deb" > "${PACKAGE_NAME}_${VERSION}_all.deb.sha512"
gpg --clearsign --default-key "$GPG_EMAIL" "${PACKAGE_NAME}_${VERSION}_all.deb.sha512"
cd ..

echo "=================================================="
echo "✅ Build Complete!"
echo "Package: $DEB_FILE"
echo "Hashsum: ${DEB_FILE}.sha512"
echo "=================================================="
