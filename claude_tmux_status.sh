#!/bin/bash
# Claude Usage Status for tmux status bar
# Returns compact usage info for tmux status line

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get usage data
output=$("$SCRIPT_DIR/claude-usage" 2>/dev/null)

# Extract key numbers
requests=$(echo "$output" | grep -E "Total requests:" | grep -oE "[0-9,]+" | head -1)
cost=$(echo "$output" | grep -E "API equivalent:" | grep -oE "\$[0-9,]+\.?[0-9]*" | head -1)

# Format for tmux status bar
if [[ -n "$requests" && -n "$cost" ]]; then
    echo "Claude: ${requests} reqs | ${cost}"
else
    echo "Claude: Loading..."
fi