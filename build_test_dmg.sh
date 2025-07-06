#!/bin/bash

# Build DMG for Claude Usage Tracker Testing

set -e

echo "Building Claude Usage Tracker DMG for testing..."

# Configuration
APP_NAME="ClaudeUsageTracker"
VERSION="1.0.0-test"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
TEMP_DIR="dmg_temp"
DIST_DIR="dist"

# Clean up any existing files
rm -rf "$TEMP_DIR" "$DIST_DIR"
mkdir -p "$TEMP_DIR" "$DIST_DIR"

# Create the DMG contents directory
DMG_CONTENTS="$TEMP_DIR/$APP_NAME"
mkdir -p "$DMG_CONTENTS"

# Copy all necessary files
echo "Copying files..."
cp claude_usage_tracker.py "$DMG_CONTENTS/"
cp claude_sync.py "$DMG_CONTENTS/"
cp claude_reconcile.py "$DMG_CONTENTS/"
cp claude_menu_bar.py "$DMG_CONTENTS/" 2>/dev/null || true
cp claude_floating_window.py "$DMG_CONTENTS/" 2>/dev/null || true
cp test_sync.py "$DMG_CONTENTS/"
cp install.sh "$DMG_CONTENTS/"
cp DMG_README.txt "$DMG_CONTENTS/README.txt"
cp sync_data_format.md "$DMG_CONTENTS/"
cp requirements.txt "$DMG_CONTENTS/" 2>/dev/null || true
cp CLAUDE.md "$DMG_CONTENTS/" 2>/dev/null || true

# Make install script executable
chmod +x "$DMG_CONTENTS/install.sh"

# Create a simple background image with instructions
cat > "$DMG_CONTENTS/INSTALL_INSTRUCTIONS.txt" << 'EOF'
CLAUDE USAGE TRACKER - QUICK INSTALL

1. Open Terminal
2. Drag install.sh to Terminal window
3. Press Enter and follow prompts

Or double-click install.sh if it opens in Terminal.

See README.txt for detailed instructions.
EOF

# Create Applications symlink for convenience
ln -s /Applications "$TEMP_DIR/Applications" 2>/dev/null || true

# Build the DMG
echo "Creating DMG..."
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$TEMP_DIR" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME"

# Clean up
rm -rf "$TEMP_DIR"

# Set proper permissions
chmod 644 "$DIST_DIR/$DMG_NAME"

echo ""
echo "✅ DMG created successfully!"
echo "📦 Location: $DIST_DIR/$DMG_NAME"
echo "📏 Size: $(du -h "$DIST_DIR/$DMG_NAME" | cut -f1)"
echo ""
echo "To test:"
echo "1. Open $DMG_NAME"
echo "2. Run the install.sh script"
echo "3. Test the claude-usage commands"
echo ""