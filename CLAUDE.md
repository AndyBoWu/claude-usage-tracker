# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Tool
```bash
# Direct execution
python3 claude_usage_tracker.py

# With command line options
python3 claude_usage_tracker.py --json
python3 claude_usage_tracker.py --start-date 2025-01-01 --end-date 2025-01-14
```

### Development Setup
```bash
# Install in development mode
pip install -e .

# Install with menu bar dependencies (macOS only)
pip install -e ".[menubar]"

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests
```bash
# Note: No tests currently exist, but when added:
python -m pytest tests/
```

### Code Formatting and Linting
```bash
# Format code with black (no config file exists yet)
black claude_usage_tracker.py claude_menu_bar.py claude_floating_window.py

# Run linting with flake8 (no config file exists yet)
flake8 claude_usage_tracker.py claude_menu_bar.py claude_floating_window.py
```

## Architecture

### Overview
This is a command-line utility that analyzes Claude Code conversation logs to track usage and calculate costs. The architecture is intentionally simple with zero core dependencies.

### Key Components
- **claude_usage_tracker.py**: Main CLI tool that reads and analyzes conversation logs
- **claude_menu_bar.py**: macOS menu bar widget (requires `rumps` library)
- **claude_floating_window.py**: Floating window UI component
- **Shell scripts**: Convenience wrappers and tmux integration

### Data Flow
1. Reads JSONL files from `~/.claude/projects/*/conversation_uuid.jsonl`
2. Parses conversation events to extract token usage
3. Calculates costs based on API pricing models
4. Generates ASCII charts and usage summaries
5. All processing happens locally with no external API calls

### Important Implementation Details
- The tool expects Claude Code conversation logs in the standard location (`~/.claude/projects/`)
- Token pricing is hardcoded in the script and may need updates as pricing changes
- The menu bar widget uses hardcoded paths to Homebrew Python (`/opt/homebrew/bin/python3.12`)
- No persistent state - analyzes logs fresh on each run
- Uses only Python standard library for core functionality to maintain zero dependencies

### Code Style
- Single-file scripts rather than modular package structure
- PEP 8 compliant (though no linting configuration exists)
- Clear function names and docstrings expected
- ASCII art for visual output