# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['claude_menu_bar_subprocess.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('claude_usage_tracker.py', '.'),  # Include the tracker script in the bundle
    ],
    hiddenimports=['zoneinfo'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Claude Usage Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Will be set by GitHub Actions or manually
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Claude Usage Tracker.app',
    icon=None,
    bundle_identifier='com.andybowu.claude-usage-tracker',
    info_plist={
        'CFBundleName': 'Claude Usage Tracker',
        'CFBundleDisplayName': 'Claude Usage Tracker',
        'CFBundleGetInfoString': 'Claude Usage Tracker 0.1.0',
        'CFBundleIdentifier': 'com.andybowu.claude-usage-tracker',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Andy Bo Wu',
        'LSUIElement': True,  # Run as menu bar app without dock icon
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
)