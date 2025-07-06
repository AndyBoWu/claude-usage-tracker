#!/bin/bash

# Build a macOS app bundle and DMG with drag-to-install interface

set -e

echo "Building Claude Usage Tracker App Bundle..."

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
SCRIPTS_DIR="$RESOURCES_DIR/scripts"
DIST_DIR="dist"

# Clean and create directories
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$MACOS_DIR" "$RESOURCES_DIR" "$SCRIPTS_DIR" "$DIST_DIR"

# Copy Python scripts to Resources
echo "Copying application files..."
cp claude_usage_tracker.py "$SCRIPTS_DIR/"
cp claude_sync.py "$SCRIPTS_DIR/"
cp claude_reconcile.py "$SCRIPTS_DIR/"
cp claude_menu_bar.py "$SCRIPTS_DIR/" 2>/dev/null || true
cp test_sync.py "$SCRIPTS_DIR/"

# Create the main executable launcher
cat > "$MACOS_DIR/ClaudeUsageTracker" << 'EOF'
#!/bin/bash

# Claude Usage Tracker Launcher
SCRIPT_DIR="$(dirname "$0")/../Resources/scripts"

# Check if Terminal is already running this script
if [[ "$TERM_PROGRAM" == "Apple_Terminal" ]] || [[ -n "$TERMINAL_EMULATOR" ]]; then
    # We're already in Terminal, run the menu
    exec python3 "$SCRIPT_DIR/launcher.py"
else
    # Open in Terminal
    osascript -e 'tell app "Terminal" to do script "'"$0"'"'
fi
EOF
chmod +x "$MACOS_DIR/ClaudeUsageTracker"

# Create a launcher menu script
cat > "$SCRIPTS_DIR/launcher.py" << 'EOF'
#!/usr/bin/env python3
"""Claude Usage Tracker - Interactive Launcher"""

import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def clear_screen():
    os.system('clear')

def print_header():
    print("=" * 60)
    print("       CLAUDE USAGE TRACKER - Multi-Mac Edition")
    print("=" * 60)
    print()

def install_commands():
    """Install command-line shortcuts"""
    print("Installing command-line tools...")
    
    # Create bin directory
    bin_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    # Create command shortcuts
    commands = {
        'claude-usage': 'python3 "{}/claude_usage_tracker.py" "$@"'.format(SCRIPT_DIR),
        'claude-sync': 'python3 "{}/claude_usage_tracker.py" --sync "$@"'.format(SCRIPT_DIR),
        'claude-reconcile': 'python3 "{}/claude_usage_tracker.py" --reconcile "$@"'.format(SCRIPT_DIR)
    }
    
    for cmd, content in commands.items():
        cmd_path = os.path.join(bin_dir, cmd)
        with open(cmd_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(content + '\n')
        os.chmod(cmd_path, 0o755)
    
    # Add to PATH if needed
    shell_rc = os.path.expanduser("~/.zshrc")
    path_line = 'export PATH="$HOME/.local/bin:$PATH"'
    
    add_to_path = True
    if os.path.exists(shell_rc):
        with open(shell_rc, 'r') as f:
            if path_line in f.read():
                add_to_path = False
    
    if add_to_path:
        with open(shell_rc, 'a') as f:
            f.write('\n# Added by Claude Usage Tracker\n')
            f.write(path_line + '\n')
        print("✅ Added ~/.local/bin to PATH")
        print("   Please run: source ~/.zshrc")
    else:
        print("✅ Commands already in PATH")
    
    print("\nCommands installed:")
    for cmd in commands:
        print(f"  • {cmd}")
    
    time.sleep(2)

def show_menu():
    while True:
        clear_screen()
        print_header()
        
        print("MAIN MENU:")
        print("1. View Usage Report")
        print("2. Sync to iCloud")
        print("3. Reconcile Multi-Mac Data")
        print("4. View Combined Report")
        print("5. Install Command-Line Tools")
        print("6. Show Sync Status")
        print("7. Help")
        print("0. Exit")
        print()
        
        choice = input("Select an option: ").strip()
        
        if choice == '1':
            clear_screen()
            print_header()
            print("LOCAL USAGE REPORT")
            print("-" * 60)
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "claude_usage_tracker.py")])
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            clear_screen()
            print_header()
            print("SYNCING TO ICLOUD...")
            print("-" * 60)
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "claude_usage_tracker.py"), "--sync"])
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            clear_screen()
            print_header()
            print("RECONCILING MULTI-MAC DATA...")
            print("-" * 60)
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "claude_usage_tracker.py"), "--reconcile"])
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            clear_screen()
            print_header()
            print("COMBINED USAGE REPORT")
            print("-" * 60)
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "claude_usage_tracker.py"), "--from-reconciled"])
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            clear_screen()
            print_header()
            install_commands()
            input("\nPress Enter to continue...")
            
        elif choice == '6':
            clear_screen()
            print_header()
            print("SYNC STATUS")
            print("-" * 60)
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "claude_usage_tracker.py"), "--sync-status"])
            input("\nPress Enter to continue...")
            
        elif choice == '7':
            clear_screen()
            print_header()
            print("HELP")
            print("-" * 60)
            print("\nMulti-Mac Setup:")
            print("1. Install on Mac #1 and sync (option 2)")
            print("2. Install on Mac #2 and sync (option 2)")
            print("3. Wait 2-5 minutes for iCloud sync")
            print("4. Reconcile data (option 3)")
            print("5. View combined report (option 4)")
            print("\nCommand-Line Usage (after installing tools):")
            print("  claude-usage     - View local usage")
            print("  claude-sync      - Sync to iCloud")
            print("  claude-reconcile - Merge all Mac data")
            input("\nPress Enter to continue...")
            
        elif choice == '0':
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        input("Press Enter to exit...")
EOF

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
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create a simple icon (you can replace this with a proper icon)
# For now, we'll create a placeholder
touch "$RESOURCES_DIR/AppIcon.icns"

# Now create the DMG with a nice background
echo "Creating DMG..."

# Create DMG source folder
DMG_SOURCE="$BUILD_DIR/dmg_source"
mkdir -p "$DMG_SOURCE"

# Copy app to DMG source
cp -R "$APP_DIR" "$DMG_SOURCE/"

# Create Applications symlink
ln -s /Applications "$DMG_SOURCE/Applications"

# Create a background folder and instructions
mkdir -p "$DMG_SOURCE/.background"

# Create a simple background with instructions (you can replace with an image)
cat > "$DMG_SOURCE/How to Install.txt" << 'EOF'
CLAUDE USAGE TRACKER - INSTALLATION

1. Drag "ClaudeUsageTracker" to the Applications folder
2. Double-click ClaudeUsageTracker in Applications to run
3. Follow the on-screen menu to set up and use

For command-line usage, select option 5 in the app menu.
EOF

# Create the DMG
DMG_NAME="ClaudeUsageTracker-${VERSION}.dmg"
hdiutil create -volname "$BUNDLE_NAME" \
    -srcfolder "$DMG_SOURCE" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "✅ App bundle and DMG created successfully!"
echo "📦 Location: $DIST_DIR/$DMG_NAME"
echo "📏 Size: $(du -h "$DIST_DIR/$DMG_NAME" | cut -f1)"
echo ""
echo "To install:"
echo "1. Open the DMG"
echo "2. Drag ClaudeUsageTracker to Applications"
echo "3. Run from Applications folder"
echo ""