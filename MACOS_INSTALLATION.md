# macOS Installation Instructions

## Important: Security Warning on First Launch

When you first download and try to open Claude Usage Tracker, you may see a security warning:

> "Claude Usage Tracker" can't be opened because Apple cannot check it for malicious software.

This is normal for apps that haven't been notarized by Apple. Here's how to open it:

### Method 1: Right-Click to Open (Recommended)
1. **Don't double-click the app**
2. Instead, **right-click** (or Control-click) on the app
3. Select **"Open"** from the context menu
4. In the dialog that appears, click **"Open"** again
5. The app will now run and be remembered as safe

### Method 2: System Settings
1. Try to open the app normally (it will be blocked)
2. Go to **System Settings** > **Privacy & Security**
3. Look for a message about Claude Usage Tracker being blocked
4. Click **"Open Anyway"**
5. Enter your password if prompted

## After First Launch

Once you've opened the app using one of the methods above, macOS will remember your choice and you can open it normally in the future.

## Why This Happens

This security warning appears because:
- The app hasn't been notarized by Apple (requires a paid developer account)
- macOS Gatekeeper protects users from potentially harmful software
- This is a common issue for open-source projects and indie developers

The app is safe to use - you can verify the source code on GitHub.

## Troubleshooting

If the app shows "Error" or "Loading..." in the menu bar:

1. **Check Claude Code is installed**: The app reads logs from `~/.claude/projects/`
2. **Ensure you have conversation history**: The app needs existing Claude Code conversations to analyze
3. **Check permissions**: The app needs read access to your home directory

## Building from Source

If you prefer to build the app yourself:

```bash
# Clone the repository
git clone https://github.com/AndyBoWu/claude-usage-tracker.git
cd claude-usage-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pyinstaller rumps

# Build the app
pyinstaller claude_usage_tracker_standalone.spec

# The app will be in dist/Claude Usage Tracker.app
```