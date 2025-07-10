# Workflow Changes Needed

This PR requires manual addition of workflow changes due to GitHub security restrictions.

## Required Change

In `.github/workflows/release.yml`, update the "Create DMG" step (around line 37-39):

### From:
```yaml
- name: Create DMG
  run: |
    ./create_dmg.sh
```

### To:
```yaml
- name: Create DMG
  run: |
    if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
      VERSION="${{ github.event.inputs.version }}" ./create_dmg.sh
    else
      ./create_dmg.sh
    fi
```

## Why This Change Is Needed

This ensures that when the workflow is manually triggered with a version input, that version is passed to the DMG creation script for correct file naming.

## How to Apply

1. Go to the Files Changed tab in this PR
2. Click "Edit file" on `.github/workflows/release.yml`
3. Make the change shown above
4. Commit to this PR branch

Note: This file will be deleted once the workflow changes are applied.