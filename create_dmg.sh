#!/bin/bash

# Claude Usage Tracker DMG Creation Script

APP_NAME="Claude Usage Tracker"
DMG_NAME="ClaudeUsageTracker"
VERSION=$(python -c "import re; content=open('setup.py').read(); print(re.search(r'version=[\"']([^\"']+)[\"']', content).group(1))")
DMG_FILE="dist/${DMG_NAME}-${VERSION}.dmg"
SOURCE_DIR="dist"
VOLUME_NAME="${APP_NAME}"

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