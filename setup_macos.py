"""
py2app setup script for Claude Usage Tracker
"""

from setuptools import setup
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

APP = ['claude_menu_bar.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'Claude Usage Tracker',
        'CFBundleDisplayName': 'Claude Usage Tracker',
        'CFBundleGetInfoString': "Claude Usage Tracker 0.1.0",
        'CFBundleIdentifier': 'com.andybowu.claude-usage-tracker',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Andy Bo Wu',
        'LSUIElement': True,  # Run as menu bar app without dock icon
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': ['rumps'],
    'includes': ['claude_usage_tracker', 'claude_floating_window'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)