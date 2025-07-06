#!/bin/bash
# Direct launcher for Claude Usage Tracker Menu Bar

# Kill any existing instances
pkill -f "claude_menu_bar.py" 2>/dev/null

# Change to the script directory
cd "$(dirname "$0")"

# Check if rumps is installed
if ! python3 -c "import rumps" 2>/dev/null; then
    echo "Installing required dependency: rumps"
    pip3 install rumps
fi

# Launch the menu bar app
echo "Starting Claude Usage Tracker Menu Bar..."
python3 claude_menu_bar.py &

echo "Menu bar app launched! Look for the icon in your menu bar."
echo "To stop it, run: pkill -f claude_menu_bar.py"