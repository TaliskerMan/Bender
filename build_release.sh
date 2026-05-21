#!/bin/bash

# Auto-increment version/build number
python3 "/Users/charlestalk/AntiGravity/workflow-tools/increment_build.py" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# build_release.sh — Automated build, sign, and hash script for Bender
set -e

# Configuration
PACKAGE_NAME="bender"
VERSION=$(head -1 debian/changelog | grep -oP '(?<=^bender \().*?(?=\))')
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
