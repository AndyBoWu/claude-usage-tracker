# Real-time Claude Usage Display Options

Three ways to keep your Claude usage visible at all times:

## 1. macOS Menu Bar App (Recommended for Mac)
Shows usage in your menu bar, updates every 5 minutes.

```bash
# Start the menu bar app
./start_menu_bar.sh

# Or run directly
python3 claude_menu_bar.py
```

Features:
- Shows requests and cost in menu bar
- Click for detailed stats
- Auto-refresh every 5 minutes
- Manual refresh option

## 2. tmux Status Bar (For Terminal Users)
Add to your `~/.tmux.conf`:

```bash
# Right side status bar
set -g status-right '#[fg=cyan]#(/Users/bo/Repos/andybowu/vibe-coding/tools/claude-usage-tracker/claude_tmux_status.sh) #[fg=default]| %H:%M'
set -g status-interval 300
```

Then reload: `tmux source-file ~/.tmux.conf`

## 3. Floating Window (Cross-platform)
A small always-on-top window you can position anywhere.

```bash
python3 claude_floating_window.py
```

Features:
- Draggable window
- Always on top
- Shows requests, cost, and daily average
- Updates every 5 minutes

## Auto-start Options

### For Menu Bar App (macOS):
Create a LaunchAgent at `~/Library/LaunchAgents/com.claude.usage.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.usage</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/bo/Repos/andybowu/vibe-coding/tools/claude-usage-tracker/claude_menu_bar.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Then: `launchctl load ~/Library/LaunchAgents/com.claude.usage.plist`

### For Floating Window:
Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Start Claude usage floating window in background
(python3 /Users/bo/Repos/andybowu/vibe-coding/tools/claude-usage-tracker/claude_floating_window.py &) >/dev/null 2>&1
```