#!/bin/bash
# Start Claude Usage Tracker Menu Bar App

cd "$(dirname "$0")"

# Install dependencies if needed
if ! python3 -c "import rumps" 2>/dev/null; then
    echo "Installing required dependency: rumps"
    pip3 install rumps
fi

# Launch the menu bar app
echo "Starting Claude Usage Tracker..."
python3 claude_menu_bar.py