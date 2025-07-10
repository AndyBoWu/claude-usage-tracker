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
