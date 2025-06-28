"""
py2app setup script for Claude Usage Tracker
"""

from setuptools import setup
import re

# Read version from setup.py
with open('setup.py', 'r') as f:
    content = f.read()
    version = re.search(r'version=["\']([^"\']+)["\']', content).group(1)

APP = ['claude_menu_bar.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': None,  # Add icon file path here if you have one
    'plist': {
        'CFBundleName': 'Claude Usage Tracker',
        'CFBundleDisplayName': 'Claude Usage Tracker',
        'CFBundleGetInfoString': f"Claude Usage Tracker {version}",
        'CFBundleIdentifier': 'com.andybowu.claude-usage-tracker',
        'CFBundleVersion': version,
        'CFBundleShortVersionString': version,
        'NSHumanReadableCopyright': 'Copyright © 2025 Andy Bo Wu',
        'LSUIElement': True,  # Run as menu bar app without dock icon
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': ['rumps'],
    'includes': ['claude_usage_tracker', 'claude_floating_window'],
}

setup(
    name='Claude Usage Tracker',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'rumps>=0.3.0',
    ],
)