Claude Usage Tracker with iCloud Sync
====================================

Version: 1.0.0 (with Multi-Mac Support)
Date: January 2025

WHAT'S NEW
----------
• iCloud sync support for multiple Macs
• Data reconciliation across devices
• Improved usage tracking and reporting

INSTALLATION
------------
1. Double-click "install.sh" to run the installer
   OR
   Open Terminal and run: ./install.sh

2. The installer will:
   - Copy files to ~/.claude-usage-tracker
   - Create command shortcuts
   - Set up iCloud sync directory

USAGE
-----
After installation, you can use these commands in Terminal:

• claude-usage         View usage statistics
• claude-sync          Sync data to iCloud  
• claude-reconcile     Merge data from all Macs
• claude-usage --from-reconciled   View combined statistics

MULTI-MAC SETUP
---------------
1. Install on Mac #1 and run: claude-sync
2. Install on Mac #2 and run: claude-sync
3. Wait 2-5 minutes for iCloud to sync
4. Run: claude-reconcile
5. View combined stats: claude-usage --from-reconciled

REQUIREMENTS
------------
• macOS 10.15 or later
• Python 3.8 or later
• iCloud Drive enabled

SUPPORT
-------
Report issues: https://github.com/anthropics/claude-code/issues

FILES INCLUDED
--------------
• install.sh - Installation script
• claude_usage_tracker.py - Main tracking tool
• claude_sync.py - iCloud sync module
• claude_reconcile.py - Data reconciliation tool
• Additional support files

UNINSTALL
---------
To remove, delete these directories:
• ~/.claude-usage-tracker
• ~/.local/bin/claude-*
• ~/Library/Mobile Documents/com~apple~CloudDocs/ClaudeUsageTracker