#!/bin/bash

# Claude Usage Tracker DMG Creation Script

APP_NAME="Claude Usage Tracker"
DMG_NAME="ClaudeUsageTracker"

# Get version from git tag, environment variable, or default
if [ -n "$GITHUB_REF" ]; then
    # Running in GitHub Actions with a tag
    VERSION="${GITHUB_REF#refs/tags/v}"
elif [ -n "$VERSION" ]; then
    # Version passed as environment variable
    VERSION="$VERSION"
else
    # Try to get version from git tag
    VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
    if [ -z "$VERSION" ]; then
        # Default version if no tag exists
        VERSION="0.1.0"
    fi
fi

DMG_FILE="dist/${DMG_NAME}-${VERSION}.dmg"
SOURCE_DIR="dist"
VOLUME_NAME="${APP_NAME}"

echo "Building DMG for version: ${VERSION}"

# Clean up any existing DMG
if [ -f "${DMG_FILE}" ]; then
    rm "${DMG_FILE}"
fi

# Create a temporary directory for DMG contents
DMG_TEMP_DIR="${SOURCE_DIR}/dmg_temp"
mkdir -p "${DMG_TEMP_DIR}"

# Copy the app to the temporary directory
cp -R "${SOURCE_DIR}/${APP_NAME}.app" "${DMG_TEMP_DIR}/"

# Create a symbolic link to Applications
ln -s /Applications "${DMG_TEMP_DIR}/Applications"

# Create the DMG
echo "Creating DMG..."
hdiutil create -volname "${VOLUME_NAME}" \
    -srcfolder "${DMG_TEMP_DIR}" \
    -ov -format UDZO \
    "${DMG_FILE}"

# Clean up
rm -rf "${DMG_TEMP_DIR}"

echo "DMG created: ${DMG_FILE}"