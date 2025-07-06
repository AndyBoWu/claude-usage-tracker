#!/bin/bash

# Claude Usage Tracker Installation Script
# This script installs the Claude Usage Tracker with iCloud sync support

set -e  # Exit on error

echo "==================================="
echo "Claude Usage Tracker Installer"
echo "==================================="
echo ""

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This installer is for macOS only."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Installation directory
INSTALL_DIR="$HOME/.claude-usage-tracker"

echo "This installer will:"
echo "1. Install Claude Usage Tracker to: $INSTALL_DIR"
echo "2. Create command-line shortcuts"
echo "3. Set up iCloud sync functionality"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy all necessary files
echo "Copying files..."
cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/*.sh "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/*.md "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/setup.py "$INSTALL_DIR/" 2>/dev/null || true

# Create bin directory for command shortcuts
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

# Create main command shortcut
echo "Creating command shortcuts..."
cat > "$BIN_DIR/claude-usage" << 'EOF'
#!/bin/bash
python3 "$HOME/.claude-usage-tracker/claude_usage_tracker.py" "$@"
EOF
chmod +x "$BIN_DIR/claude-usage"

# Create sync command shortcut
cat > "$BIN_DIR/claude-sync" << 'EOF'
#!/bin/bash
python3 "$HOME/.claude-usage-tracker/claude_usage_tracker.py" --sync "$@"
EOF
chmod +x "$BIN_DIR/claude-sync"

# Create reconcile command shortcut
cat > "$BIN_DIR/claude-reconcile" << 'EOF'
#!/bin/bash
python3 "$HOME/.claude-usage-tracker/claude_usage_tracker.py" --reconcile "$@"
EOF
chmod +x "$BIN_DIR/claude-reconcile"

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install Python dependencies if needed
echo "Checking Python dependencies..."
if python3 -c "import rumps" 2>/dev/null; then
    echo "Menu bar dependencies already installed."
else
    echo "Installing menu bar dependencies..."
    pip3 install rumps || echo "Warning: Failed to install menu bar dependencies"
fi

# Add bin directory to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "Adding $BIN_DIR to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "Please run: source ~/.zshrc"
    echo "Or restart your terminal for PATH changes to take effect."
fi

# Initialize iCloud sync directory
echo ""
echo "Setting up iCloud sync..."
python3 "$INSTALL_DIR/claude_usage_tracker.py" --sync-status >/dev/null 2>&1 || true

echo ""
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo ""
echo "Available commands:"
echo "  claude-usage          - View usage statistics"
echo "  claude-sync           - Sync data to iCloud"
echo "  claude-reconcile      - Reconcile data from multiple Macs"
echo ""
echo "Quick start:"
echo "  1. Run 'claude-sync' to sync your current Mac's data"
echo "  2. Repeat on your other Mac(s)"
echo "  3. Run 'claude-reconcile' to merge data from all Macs"
echo "  4. Run 'claude-usage --from-reconciled' to view combined stats"
echo ""
echo "For menu bar widget (optional):"
echo "  cd $INSTALL_DIR && python3 claude_menu_bar.py"
echo ""