#!/bin/bash
# Fix and rebuild Claude Usage Tracker

echo "🔧 Fixing Claude Usage Tracker Menu Bar App..."

# Remove old app
if [ -d "/Applications/Claude Usage Tracker.app" ]; then
    echo "Removing old app..."
    rm -rf "/Applications/Claude Usage Tracker.app"
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install rumps pyinstaller

# Build new app
echo "Building new app..."
if [ -f "claude_usage_tracker_standalone.spec" ]; then
    pyinstaller --clean claude_usage_tracker_standalone.spec
else
    # Create a minimal spec file if it doesn't exist
    pyinstaller --onefile --windowed --name "Claude Usage Tracker" \
        --icon-file images/icon.icns \
        --osx-bundle-identifier com.claudeusagetracker.app \
        claude_menu_bar.py
fi

# Install to Applications
if [ -d "dist/Claude Usage Tracker.app" ]; then
    echo "Installing to Applications..."
    cp -R "dist/Claude Usage Tracker.app" /Applications/
    
    # Remove quarantine
    xattr -cr "/Applications/Claude Usage Tracker.app"
    
    echo "✅ Done! Try opening from Applications folder."
else
    echo "❌ Build failed. Please check for errors above."
fi