# Fix: Pass version to DMG creation in GitHub Actions

## Summary
Updates the GitHub Actions workflow to pass the version to `create_dmg.sh` when triggered via workflow_dispatch.

## Changes
```yaml
- name: Create DMG
  run: |
    if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
      VERSION="${{ github.event.inputs.version }}" ./create_dmg.sh
    else
      ./create_dmg.sh
    fi
```

## Why this is needed
Without this change, manually triggered workflows won't pass the version to the DMG creation script, potentially resulting in incorrectly named release assets.

## What was already done
- `create_dmg.sh` was already updated to accept VERSION from environment (commit 397e291)
- This PR completes the integration by having the workflow pass the version

## Test plan
- [ ] Manual workflow dispatch with version input creates DMG with correct filename
- [ ] Tag-triggered workflows continue to work as before

## How to apply this change
Since workflow files require special permissions, you can:
1. Apply this change directly through GitHub's web interface
2. Copy the change from the local branch: `fix/workflow-dmg-version`