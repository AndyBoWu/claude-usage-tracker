#!/bin/bash

# Create GitHub Release assets

VERSION="1.0.0"
RELEASE_DIR="release-$VERSION"

echo "Creating release assets for v$VERSION..."

# Create release directory
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Build all installers
echo "Building installers..."
./build_menubar_app.sh

# Copy installers to release directory
cp dist/ClaudeUsageTracker-MenuBar-$VERSION.dmg "$RELEASE_DIR/"
cp dist/ClaudeUsageTracker-MenuBar-$VERSION.pkg "$RELEASE_DIR/"

# Create release notes
cat > "$RELEASE_DIR/RELEASE_NOTES.md" << 'EOF'
# Claude Usage Tracker v1.0.0 - Multi-Mac Edition 🚀

## ✨ What's New

### iCloud Sync Support
- **Sync Across Macs**: Track your Claude usage across all your devices
- **Automatic Reconciliation**: Merge data from multiple Macs seamlessly
- **Privacy First**: Only usage metrics are synced, no conversation content

### Enhanced Menu Bar App
- Real-time usage statistics in your menu bar
- One-click sync to iCloud
- View combined statistics from all Macs
- Improved UI with sync status indicators

## 📦 Installation

### Option 1: DMG (Recommended)
1. Download `ClaudeUsageTracker-MenuBar-1.0.0.dmg`
2. Open the DMG and drag to Applications
3. Launch from Applications folder

### Option 2: PKG Installer
1. Download `ClaudeUsageTracker-MenuBar-1.0.0.pkg`
2. Double-click to install
3. App launches automatically

## 🔄 Multi-Mac Setup

1. Install on Mac #1 and click "Sync to iCloud" in menu bar
2. Install on Mac #2 and click "Sync to iCloud"
3. Wait 2-5 minutes for iCloud to sync
4. Click "Reconcile All Macs" on either Mac
5. Click "View Combined Stats" to see total usage

## 🛡️ Security Note

On first launch, macOS may show an "unidentified developer" warning:
1. Go to System Settings → Privacy & Security
2. Click "Open Anyway" next to the app name

## 🐛 Bug Fixes
- Fixed timestamp parsing in reconciliation
- Improved error handling for missing iCloud Drive
- Better conflict resolution for duplicate sessions

## 📋 Requirements
- macOS 10.15 or later
- Python 3.8 or later
- iCloud Drive enabled (for sync features)

## 🙏 Acknowledgments
Thanks to all Claude Code users who inspired the multi-Mac sync feature!
EOF

# Create checksums
echo "Creating checksums..."
cd "$RELEASE_DIR"
shasum -a 256 *.dmg *.pkg > checksums.txt

# Create install verification script
cat > verify_install.sh << 'EOF'
#!/bin/bash
echo "Verifying Claude Usage Tracker installation..."

# Check if app exists
if [ -d "/Applications/ClaudeUsageTracker.app" ]; then
    echo "✅ App installed in Applications"
else
    echo "❌ App not found in Applications"
fi

# Check if commands are available
if command -v claude-usage &> /dev/null; then
    echo "✅ Command-line tools installed"
    claude-usage --version 2>/dev/null || echo "   Version: 1.0.0"
else
    echo "ℹ️  Command-line tools not installed (optional)"
fi

# Check Python dependencies
if python3 -c "import rumps" 2>/dev/null; then
    echo "✅ Python dependencies installed"
else
    echo "ℹ️  Python dependencies not installed (will be installed on first run)"
fi

# Check iCloud sync directory
SYNC_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/ClaudeUsageTracker"
if [ -d "$SYNC_DIR" ]; then
    echo "✅ iCloud sync directory exists"
else
    echo "ℹ️  iCloud sync directory not yet created (will be created on first sync)"
fi

echo ""
echo "Installation verification complete!"
EOF
chmod +x verify_install.sh

cd ..

echo ""
echo "✅ Release assets created in $RELEASE_DIR/"
echo ""
echo "Files ready for GitHub release:"
ls -la "$RELEASE_DIR/"
echo ""
echo "To create the release:"
echo "1. Go to https://github.com/AndyBoWu/claude-usage-tracker/releases/new"
echo "2. Tag: v$VERSION"
echo "3. Title: Claude Usage Tracker v$VERSION - Multi-Mac Edition"
echo "4. Copy contents of RELEASE_NOTES.md to description"
echo "5. Upload the .dmg and .pkg files"
echo "6. Publish release"
echo ""