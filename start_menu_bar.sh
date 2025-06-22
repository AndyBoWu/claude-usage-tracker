#!/bin/bash
# Start Claude Usage Menu Bar App

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use the Homebrew Python which has rumps installed
exec /opt/homebrew/opt/python@3.12/bin/python3.12 "$SCRIPT_DIR/claude_menu_bar.py"