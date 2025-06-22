# tmux Claude Usage Status Setup

Add this to your `~/.tmux.conf` to display Claude usage in your tmux status bar:

```bash
# Claude usage in status bar (updates every 1 minute)
set -g status-right '#[fg=cyan]#(/Users/bo/Repos/andybowu/vibe-coding/tools/claude-usage-tracker/claude_tmux_status.sh) #[fg=default]| %H:%M'
set -g status-interval 60  # Update every 1 minute
```

Or if you want it on the left side:
```bash
set -g status-left '#[fg=cyan]#(/Users/bo/Repos/andybowu/vibe-coding/tools/claude-usage-tracker/claude_tmux_status.sh) #[fg=default]| '
```

After adding, reload tmux config:
```bash
tmux source-file ~/.tmux.conf
```