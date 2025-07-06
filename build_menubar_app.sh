#!/bin/bash

# Build macOS Menu Bar App with proper app bundle

set -e

echo "Building Claude Usage Tracker Menu Bar App..."

# Configuration
APP_NAME="Claude Usage Tracker"
BUNDLE_NAME="ClaudeUsageTracker"
VERSION="1.0.0"
BUNDLE_ID="com.anthropic.claude-usage-tracker"

# Directories
BUILD_DIR="build"
APP_DIR="$BUILD_DIR/$BUNDLE_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
DIST_DIR="dist"

# Clean and create directories
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$MACOS_DIR" "$RESOURCES_DIR" "$DIST_DIR"

# Copy Python scripts to Resources
echo "Copying application files..."
cp claude_usage_tracker.py "$RESOURCES_DIR/"
cp claude_sync.py "$RESOURCES_DIR/"
cp claude_reconcile.py "$RESOURCES_DIR/"
cp claude_menu_bar.py "$RESOURCES_DIR/"
cp claude_floating_window.py "$RESOURCES_DIR/" 2>/dev/null || true
cp sync_data_format.md "$RESOURCES_DIR/" 2>/dev/null || true
cp CLAUDE.md "$RESOURCES_DIR/" 2>/dev/null || true

# Create the main executable that launches the menu bar app
cat > "$MACOS_DIR/ClaudeUsageTracker" << 'EOF'
#!/bin/bash

# Get the Resources directory path
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"

# Check if rumps is installed
if ! python3 -c "import rumps" 2>/dev/null; then
    # Show dialog asking to install dependencies
    osascript -e 'display dialog "Claude Usage Tracker needs to install Python dependencies.\n\nClick OK to install (requires internet connection)." buttons {"Cancel", "OK"} default button "OK" with icon caution'
    if [ $? -eq 0 ]; then
        # Install rumps
        osascript -e 'do shell script "pip3 install rumps" with administrator privileges'
    else
        exit 1
    fi
fi

# Launch the menu bar app
cd "$DIR"
exec python3 claude_menu_bar.py
EOF
chmod +x "$MACOS_DIR/ClaudeUsageTracker"

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>ClaudeUsageTracker</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create a simple icon placeholder
touch "$RESOURCES_DIR/AppIcon.icns"

# Create an installer script inside the app
cat > "$RESOURCES_DIR/install_cli_tools.sh" << 'EOF'
#!/bin/bash

# Install command-line tools for Claude Usage Tracker

echo "Installing Claude Usage Tracker CLI tools..."

# Get the Resources directory
RESOURCES_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create local bin directory
mkdir -p "$HOME/.local/bin"

# Create command shortcuts
cat > "$HOME/.local/bin/claude-usage" << EOL
#!/bin/bash
python3 "$RESOURCES_DIR/claude_usage_tracker.py" "\$@"
EOL
chmod +x "$HOME/.local/bin/claude-usage"

cat > "$HOME/.local/bin/claude-sync" << EOL
#!/bin/bash
python3 "$RESOURCES_DIR/claude_usage_tracker.py" --sync "\$@"
EOL
chmod +x "$HOME/.local/bin/claude-sync"

cat > "$HOME/.local/bin/claude-reconcile" << EOL
#!/bin/bash
python3 "$RESOURCES_DIR/claude_usage_tracker.py" --reconcile "\$@"
EOL
chmod +x "$HOME/.local/bin/claude-reconcile"

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "Added ~/.local/bin to PATH in ~/.zshrc"
    echo "Please run: source ~/.zshrc"
fi

echo "✅ CLI tools installed successfully!"
echo ""
echo "Available commands:"
echo "  claude-usage     - View usage statistics"
echo "  claude-sync      - Sync data to iCloud"
echo "  claude-reconcile - Reconcile data from multiple Macs"
EOF
chmod +x "$RESOURCES_DIR/install_cli_tools.sh"

# Now create the DMG with the app
echo "Creating DMG..."

# Create DMG source folder
DMG_SOURCE="$BUILD_DIR/dmg_source"
mkdir -p "$DMG_SOURCE/.background"

# Copy app to DMG source
cp -R "$APP_DIR" "$DMG_SOURCE/"

# Create Applications symlink
ln -s /Applications "$DMG_SOURCE/Applications"

# Create installation instructions
cat > "$DMG_SOURCE/How to Install.txt" << 'EOF'
CLAUDE USAGE TRACKER - MENU BAR APP

Installation:
1. Drag ClaudeUsageTracker to your Applications folder
2. Double-click to launch (it will appear in your menu bar)
3. Click the menu bar icon to see usage statistics

Features:
• Real-time usage tracking in menu bar
• iCloud sync across multiple Macs
• Detailed cost breakdowns
• Command-line tools (optional)

First Run:
- May need to approve in System Settings > Privacy & Security
- Will ask to install Python dependencies if needed

To install command-line tools:
Right-click the app → Show Package Contents → Contents → Resources → install_cli_tools.sh
EOF

# Create a simple background image with text (you can replace with a proper image)
cat > "$DMG_SOURCE/.background/background.txt" << 'EOF'
Drag ClaudeUsageTracker to Applications →
EOF

# Create the DMG
DMG_NAME="${BUNDLE_NAME}-MenuBar-${VERSION}.dmg"
hdiutil create -volname "$BUNDLE_NAME" \
    -srcfolder "$DMG_SOURCE" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME"

# Also create a simple installer package
echo "Creating installer package..."
INSTALLER_DIR="$BUILD_DIR/installer"
PAYLOAD_DIR="$INSTALLER_DIR/payload"
SCRIPTS_DIR="$INSTALLER_DIR/scripts"

mkdir -p "$PAYLOAD_DIR/Applications" "$SCRIPTS_DIR"
cp -R "$APP_DIR" "$PAYLOAD_DIR/Applications/"

# Create postinstall script
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash

# Launch the app after installation
open -a "Claude Usage Tracker" || true

exit 0
EOF
chmod +x "$SCRIPTS_DIR/postinstall"

# Build the installer package
pkgbuild --root "$PAYLOAD_DIR" \
         --identifier "$BUNDLE_ID" \
         --version "$VERSION" \
         --scripts "$SCRIPTS_DIR" \
         --install-location "/" \
         "$DIST_DIR/${BUNDLE_NAME}-MenuBar-${VERSION}.pkg"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "✅ Menu Bar App created successfully!"
echo ""
echo "📦 Created two installers:"
echo "   1. DMG: $DIST_DIR/$DMG_NAME"
echo "      Size: $(du -h "$DIST_DIR/$DMG_NAME" | cut -f1)"
echo ""
echo "   2. PKG: $DIST_DIR/${BUNDLE_NAME}-MenuBar-${VERSION}.pkg"
echo "      Size: $(du -h "$DIST_DIR/${BUNDLE_NAME}-MenuBar-${VERSION}.pkg" | cut -f1)"
echo ""
echo "The app will run in the menu bar (top-right of screen)"
echo "showing real-time Claude usage statistics."
echo ""