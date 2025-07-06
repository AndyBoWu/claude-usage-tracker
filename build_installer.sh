#!/bin/bash

# Build a proper macOS installer package (.pkg)

set -e

echo "Building Claude Usage Tracker macOS Installer..."

# Configuration
APP_NAME="Claude Usage Tracker"
APP_ID="com.anthropic.claude-usage-tracker"
VERSION="1.0.0"
INSTALLER_NAME="ClaudeUsageTracker-${VERSION}.pkg"

# Directories
BUILD_DIR="build"
SCRIPTS_DIR="$BUILD_DIR/scripts"
PAYLOAD_DIR="$BUILD_DIR/payload"
DIST_DIR="dist"

# Clean and create directories
rm -rf "$BUILD_DIR" 
mkdir -p "$BUILD_DIR" "$SCRIPTS_DIR" "$PAYLOAD_DIR" "$DIST_DIR"

# Create installation directories in payload
INSTALL_ROOT="$PAYLOAD_DIR/usr/local/claude-usage-tracker"
BIN_DIR="$PAYLOAD_DIR/usr/local/bin"
mkdir -p "$INSTALL_ROOT" "$BIN_DIR"

# Copy application files to payload
echo "Copying application files..."
cp claude_usage_tracker.py "$INSTALL_ROOT/"
cp claude_sync.py "$INSTALL_ROOT/"
cp claude_reconcile.py "$INSTALL_ROOT/"
cp claude_menu_bar.py "$INSTALL_ROOT/" 2>/dev/null || true
cp claude_floating_window.py "$INSTALL_ROOT/" 2>/dev/null || true
cp test_sync.py "$INSTALL_ROOT/"
cp sync_data_format.md "$INSTALL_ROOT/"
cp CLAUDE.md "$INSTALL_ROOT/" 2>/dev/null || true
cp requirements.txt "$INSTALL_ROOT/" 2>/dev/null || true

# Create wrapper scripts in /usr/local/bin
cat > "$BIN_DIR/claude-usage" << 'EOF'
#!/bin/bash
exec python3 /usr/local/claude-usage-tracker/claude_usage_tracker.py "$@"
EOF
chmod +x "$BIN_DIR/claude-usage"

cat > "$BIN_DIR/claude-sync" << 'EOF'
#!/bin/bash
exec python3 /usr/local/claude-usage-tracker/claude_usage_tracker.py --sync "$@"
EOF
chmod +x "$BIN_DIR/claude-sync"

cat > "$BIN_DIR/claude-reconcile" << 'EOF'
#!/bin/bash
exec python3 /usr/local/claude-usage-tracker/claude_usage_tracker.py --reconcile "$@"
EOF
chmod +x "$BIN_DIR/claude-reconcile"

# Create postinstall script
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash

# Initialize iCloud sync directory
echo "Setting up Claude Usage Tracker..."
python3 /usr/local/claude-usage-tracker/claude_usage_tracker.py --sync-status >/dev/null 2>&1 || true

# Install Python dependencies if needed
if ! python3 -c "import rumps" 2>/dev/null; then
    echo "Installing optional menu bar dependencies..."
    pip3 install rumps 2>/dev/null || true
fi

echo "Installation complete!"
echo ""
echo "Available commands:"
echo "  claude-usage     - View usage statistics"
echo "  claude-sync      - Sync data to iCloud"
echo "  claude-reconcile - Reconcile data from multiple Macs"

exit 0
EOF
chmod +x "$SCRIPTS_DIR/postinstall"

# Create the component package
echo "Building component package..."
pkgbuild --root "$PAYLOAD_DIR" \
         --identifier "$APP_ID" \
         --version "$VERSION" \
         --scripts "$SCRIPTS_DIR" \
         --install-location "/" \
         "$BUILD_DIR/claude-usage-tracker.pkg"

# Create distribution XML
cat > "$BUILD_DIR/distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2.0">
    <title>Claude Usage Tracker</title>
    <organization>com.anthropic</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="true" rootVolumeOnly="true"/>
    <welcome file="welcome.html" mime-type="text/html"/>
    <readme file="readme.html" mime-type="text/html"/>
    <license file="license.html" mime-type="text/html"/>
    <background file="background.png" alignment="bottomleft" scaling="none"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.anthropic.claude-usage-tracker"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.anthropic.claude-usage-tracker" visible="false">
        <pkg-ref id="com.anthropic.claude-usage-tracker"/>
    </choice>
    <pkg-ref id="com.anthropic.claude-usage-tracker" version="$VERSION" onConclusion="none">claude-usage-tracker.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome message
cat > "$BUILD_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h2 { color: #333; }
        p { line-height: 1.5; }
    </style>
</head>
<body>
    <h2>Welcome to Claude Usage Tracker</h2>
    <p>This installer will set up the Claude Usage Tracker with iCloud sync support on your Mac.</p>
    <p><strong>Features:</strong></p>
    <ul>
        <li>Track Claude Code usage and costs</li>
        <li>Sync data across multiple Macs via iCloud</li>
        <li>Generate detailed usage reports</li>
        <li>Command-line tools for easy access</li>
    </ul>
    <p>Click Continue to proceed with the installation.</p>
</body>
</html>
EOF

# Create readme
cat > "$BUILD_DIR/readme.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h2 { color: #333; }
        code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h2>Getting Started</h2>
    <p>After installation, the following commands will be available in Terminal:</p>
    <pre>
claude-usage          # View usage statistics
claude-sync           # Sync data to iCloud
claude-reconcile      # Reconcile data from multiple Macs
    </pre>
    
    <h2>Multi-Mac Setup</h2>
    <ol>
        <li>Install on Mac #1 and run: <code>claude-sync</code></li>
        <li>Install on Mac #2 and run: <code>claude-sync</code></li>
        <li>Wait 2-5 minutes for iCloud to sync</li>
        <li>Run: <code>claude-reconcile</code></li>
        <li>View combined stats: <code>claude-usage --from-reconciled</code></li>
    </ol>
    
    <h2>Requirements</h2>
    <ul>
        <li>macOS 10.15 or later</li>
        <li>Python 3.8 or later</li>
        <li>iCloud Drive enabled for sync features</li>
    </ul>
</body>
</html>
EOF

# Create a simple license file
cat > "$BUILD_DIR/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <h2>MIT License</h2>
    <p>Copyright (c) 2025 Anthropic</p>
    <p>Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:</p>
    <p>The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.</p>
    <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.</p>
</body>
</html>
EOF

# Build the final installer package
echo "Building final installer..."
productbuild --distribution "$BUILD_DIR/distribution.xml" \
             --package-path "$BUILD_DIR" \
             --resources "$BUILD_DIR" \
             "$DIST_DIR/$INSTALLER_NAME"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "✅ Installer created successfully!"
echo "📦 Location: $DIST_DIR/$INSTALLER_NAME"
echo "📏 Size: $(du -h "$DIST_DIR/$INSTALLER_NAME" | cut -f1)"
echo ""
echo "To install: Double-click the .pkg file"
echo ""