# Claude Usage Tracker Sync Data Format

## Overview

This document defines the JSON data format for synchronizing Claude usage data across multiple machines. The sync system consists of three main components:

1. **Machine Sync Files**: Individual files uploaded by each machine containing their usage data
2. **Manifest File**: Central registry tracking all machines and their sync status
3. **Sync State**: Metadata for supporting incremental synchronization

## Design Principles

- **Incremental Sync**: Only new data is uploaded to minimize bandwidth
- **Conflict Resolution**: Sessions used on multiple machines are merged by timestamp
- **Privacy First**: No conversation content is synced, only usage metrics
- **Forward Compatible**: Version field allows format evolution
- **Compression Ready**: JSON structure optimized for gzip compression

## File Naming Conventions

```
sync/
├── manifest.json                          # Central manifest file
├── machines/
│   ├── {machine_uuid}.json               # Current sync data for each machine
│   └── {machine_uuid}.{timestamp}.json   # Historical snapshots (optional)
└── archive/
    └── {year}/{month}/                   # Archived data organized by date
```

## 1. Machine Sync File Schema

Each machine uploads a JSON file containing its usage data and sync state.

### Schema

```json
{
  "$schema": "https://claude-usage-tracker.com/schemas/v1/machine-sync.json",
  "version": "1.0",
  "machine": {
    "uuid": "string (UUID v4)",
    "hostname": "string",
    "platform": "string (darwin|linux|win32)",
    "os_version": "string",
    "tracker_version": "string",
    "created_at": "ISO 8601 timestamp",
    "updated_at": "ISO 8601 timestamp"
  },
  "sync_metadata": {
    "last_full_sync": "ISO 8601 timestamp",
    "last_incremental_sync": "ISO 8601 timestamp",
    "total_sessions": "integer",
    "total_usage_records": "integer",
    "sync_mode": "full|incremental"
  },
  "usage_summary": {
    "total_requests": "integer",
    "total_input_tokens": "integer",
    "total_output_tokens": "integer",
    "total_cache_creation_tokens": "integer",
    "total_cache_read_tokens": "integer",
    "total_cost_usd": "number",
    "first_usage": "ISO 8601 timestamp",
    "last_usage": "ISO 8601 timestamp"
  },
  "sessions": {
    "{session_id}": {
      "project_name": "string",
      "first_seen": "ISO 8601 timestamp",
      "last_updated": "ISO 8601 timestamp",
      "usage_count": "integer",
      "sync_state": {
        "last_synced_timestamp": "ISO 8601 timestamp",
        "last_synced_index": "integer",
        "checksum": "string (SHA-256 of usage records)"
      },
      "usage_records": [
        {
          "timestamp": "ISO 8601 timestamp",
          "model": "string",
          "input_tokens": "integer",
          "output_tokens": "integer",
          "cache_creation_tokens": "integer",
          "cache_read_tokens": "integer",
          "cost_usd": "number",
          "index": "integer (position in original log file)"
        }
      ],
      "summary": {
        "total_requests": "integer",
        "total_input_tokens": "integer",
        "total_output_tokens": "integer",
        "total_cache_creation_tokens": "integer",
        "total_cache_read_tokens": "integer",
        "total_cost_usd": "number",
        "models_used": ["string"]
      }
    }
  }
}
```

### Example Machine Sync File

```json
{
  "$schema": "https://claude-usage-tracker.com/schemas/v1/machine-sync.json",
  "version": "1.0",
  "machine": {
    "uuid": "a7c4f9e1-2b3d-4e5f-6a7b-8c9d0e1f2a3b",
    "hostname": "macbook-pro.local",
    "platform": "darwin",
    "os_version": "Darwin 24.5.0",
    "tracker_version": "1.0.0",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-06T15:30:00Z"
  },
  "sync_metadata": {
    "last_full_sync": "2025-01-01T10:00:00Z",
    "last_incremental_sync": "2025-01-06T15:30:00Z",
    "total_sessions": 3,
    "total_usage_records": 127,
    "sync_mode": "incremental"
  },
  "usage_summary": {
    "total_requests": 127,
    "total_input_tokens": 1250000,
    "total_output_tokens": 875000,
    "total_cache_creation_tokens": 125000,
    "total_cache_read_tokens": 95000,
    "total_cost_usd": 45.75,
    "first_usage": "2025-01-01T10:15:00Z",
    "last_usage": "2025-01-06T15:25:00Z"
  },
  "sessions": {
    "conversation_abc123": {
      "project_name": "claude-usage-tracker",
      "first_seen": "2025-01-01T10:15:00Z",
      "last_updated": "2025-01-06T14:30:00Z",
      "usage_count": 45,
      "sync_state": {
        "last_synced_timestamp": "2025-01-06T14:30:00Z",
        "last_synced_index": 45,
        "checksum": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
      },
      "usage_records": [
        {
          "timestamp": "2025-01-06T14:25:00Z",
          "model": "claude-sonnet-4-20250514",
          "input_tokens": 2500,
          "output_tokens": 1800,
          "cache_creation_tokens": 300,
          "cache_read_tokens": 150,
          "cost_usd": 0.0345,
          "index": 44
        },
        {
          "timestamp": "2025-01-06T14:30:00Z",
          "model": "claude-sonnet-4-20250514",
          "input_tokens": 1200,
          "output_tokens": 950,
          "cache_creation_tokens": 0,
          "cache_read_tokens": 450,
          "cost_usd": 0.0198,
          "index": 45
        }
      ],
      "summary": {
        "total_requests": 45,
        "total_input_tokens": 450000,
        "total_output_tokens": 325000,
        "total_cache_creation_tokens": 45000,
        "total_cache_read_tokens": 35000,
        "total_cost_usd": 15.25,
        "models_used": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]
      }
    },
    "conversation_def456": {
      "project_name": "my-web-app",
      "first_seen": "2025-01-03T09:00:00Z",
      "last_updated": "2025-01-05T16:45:00Z",
      "usage_count": 62,
      "sync_state": {
        "last_synced_timestamp": "2025-01-05T16:45:00Z",
        "last_synced_index": 62,
        "checksum": "b2c3d4e5f67890123456789012345678901bcdef2345678901bcdef234567890"
      },
      "usage_records": [],
      "summary": {
        "total_requests": 62,
        "total_input_tokens": 620000,
        "total_output_tokens": 430000,
        "total_cache_creation_tokens": 62000,
        "total_cache_read_tokens": 48000,
        "total_cost_usd": 22.50,
        "models_used": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
      }
    }
  }
}
```

## 2. Manifest File Schema

The manifest file tracks all machines and provides a global view of usage across the fleet.

### Schema

```json
{
  "$schema": "https://claude-usage-tracker.com/schemas/v1/manifest.json",
  "version": "1.0",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",
  "machines": {
    "{machine_uuid}": {
      "hostname": "string",
      "platform": "string",
      "first_seen": "ISO 8601 timestamp",
      "last_sync": "ISO 8601 timestamp",
      "last_sync_mode": "full|incremental",
      "status": "active|inactive|error",
      "error_message": "string (optional)",
      "usage_summary": {
        "total_requests": "integer",
        "total_cost_usd": "number",
        "last_usage": "ISO 8601 timestamp"
      }
    }
  },
  "global_summary": {
    "total_machines": "integer",
    "active_machines": "integer",
    "total_requests": "integer",
    "total_input_tokens": "integer",
    "total_output_tokens": "integer",
    "total_cache_creation_tokens": "integer",
    "total_cache_read_tokens": "integer",
    "total_cost_usd": "number",
    "first_usage": "ISO 8601 timestamp",
    "last_usage": "ISO 8601 timestamp",
    "last_updated": "ISO 8601 timestamp"
  },
  "sessions_index": {
    "{session_id}": {
      "machines": ["machine_uuid"],
      "project_name": "string",
      "first_seen": "ISO 8601 timestamp",
      "last_updated": "ISO 8601 timestamp",
      "total_usage_count": "integer",
      "conflict_status": "none|resolved|pending"
    }
  }
}
```

### Example Manifest File

```json
{
  "$schema": "https://claude-usage-tracker.com/schemas/v1/manifest.json",
  "version": "1.0",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-06T16:00:00Z",
  "machines": {
    "a7c4f9e1-2b3d-4e5f-6a7b-8c9d0e1f2a3b": {
      "hostname": "macbook-pro.local",
      "platform": "darwin",
      "first_seen": "2025-01-01T10:00:00Z",
      "last_sync": "2025-01-06T15:30:00Z",
      "last_sync_mode": "incremental",
      "status": "active",
      "usage_summary": {
        "total_requests": 127,
        "total_cost_usd": 45.75,
        "last_usage": "2025-01-06T15:25:00Z"
      }
    },
    "b8d5f0e2-3c4e-5f6g-7b8c-9d0e1f2b4c5d": {
      "hostname": "ubuntu-desktop",
      "platform": "linux",
      "first_seen": "2025-01-02T08:00:00Z",
      "last_sync": "2025-01-06T12:00:00Z",
      "last_sync_mode": "full",
      "status": "active",
      "usage_summary": {
        "total_requests": 89,
        "total_cost_usd": 32.40,
        "last_usage": "2025-01-06T11:45:00Z"
      }
    },
    "c9e6f1e3-4d5f-6g7h-8c9d-0e1f2c5d6e7f": {
      "hostname": "old-laptop",
      "platform": "win32",
      "first_seen": "2025-01-01T12:00:00Z",
      "last_sync": "2025-01-03T10:00:00Z",
      "last_sync_mode": "full",
      "status": "inactive",
      "usage_summary": {
        "total_requests": 15,
        "total_cost_usd": 5.25,
        "last_usage": "2025-01-03T09:30:00Z"
      }
    }
  },
  "global_summary": {
    "total_machines": 3,
    "active_machines": 2,
    "total_requests": 231,
    "total_input_tokens": 2150000,
    "total_output_tokens": 1525000,
    "total_cache_creation_tokens": 215000,
    "total_cache_read_tokens": 165000,
    "total_cost_usd": 83.40,
    "first_usage": "2025-01-01T10:15:00Z",
    "last_usage": "2025-01-06T15:25:00Z",
    "last_updated": "2025-01-06T16:00:00Z"
  },
  "sessions_index": {
    "conversation_abc123": {
      "machines": ["a7c4f9e1-2b3d-4e5f-6a7b-8c9d0e1f2a3b"],
      "project_name": "claude-usage-tracker",
      "first_seen": "2025-01-01T10:15:00Z",
      "last_updated": "2025-01-06T14:30:00Z",
      "total_usage_count": 45,
      "conflict_status": "none"
    },
    "conversation_def456": {
      "machines": ["a7c4f9e1-2b3d-4e5f-6a7b-8c9d0e1f2a3b", "b8d5f0e2-3c4e-5f6g-7b8c-9d0e1f2b4c5d"],
      "project_name": "my-web-app",
      "first_seen": "2025-01-03T09:00:00Z",
      "last_updated": "2025-01-05T16:45:00Z",
      "total_usage_count": 98,
      "conflict_status": "resolved"
    }
  }
}
```

## 3. Incremental Sync Strategy

### Sync State Tracking

Each session maintains sync state to enable incremental updates:

```json
"sync_state": {
  "last_synced_timestamp": "2025-01-06T14:30:00Z",
  "last_synced_index": 45,
  "checksum": "SHA-256 hash of all synced usage records"
}
```

### Incremental Update Process

1. **Client Side**:
   - Read local JSONL files
   - Compare timestamps with last_synced_timestamp
   - Include only new records (timestamp > last_synced_timestamp)
   - Update sync_state after successful upload

2. **Server Side**:
   - Validate checksum for data integrity
   - Merge new records with existing data
   - Update manifest with latest sync info
   - Handle conflicts if session exists on multiple machines

### Conflict Resolution

When the same session_id appears on multiple machines:

1. **Merge by Timestamp**: Records are merged chronologically
2. **Duplicate Detection**: Same timestamp + model + tokens = duplicate (keep one)
3. **Checksum Validation**: Ensure data integrity across machines
4. **Conflict Logging**: Track resolution in manifest for debugging

## 4. Privacy and Security Considerations

### Data Minimization

- **No Conversation Content**: Only usage metrics are synced
- **No Personal Data**: Project names are sanitized if needed
- **Optional Fields**: Hostname can be anonymized

### Recommended Security Measures

```json
{
  "privacy_settings": {
    "anonymize_hostname": true,
    "exclude_project_names": false,
    "encryption": "transit|at-rest|both",
    "retention_days": 365
  }
}
```

## 5. Compression and Storage

### File Size Optimization

- **Incremental Records Only**: Reduces payload size by 90%+
- **Summary-Only Mode**: Option to sync only summaries, not detailed records
- **Gzip Compression**: JSON compresses well, expect 70-80% reduction

### Example Compressed Sizes

- Full sync file: ~500KB → ~100KB gzipped
- Incremental update: ~50KB → ~10KB gzipped
- Manifest file: ~20KB → ~5KB gzipped

## 6. Version Compatibility

### Version Field

All files include a version field for forward compatibility:

```json
"version": "1.0"
```

### Migration Strategy

1. **Minor Updates (1.0 → 1.1)**: Add new optional fields
2. **Major Updates (1.x → 2.0)**: Provide migration tool
3. **Backwards Compatibility**: Readers should ignore unknown fields

### Version History

- **1.0** (2025-01): Initial format
- Future versions will be documented here

## 7. Implementation Notes

### File Operations

1. **Atomic Writes**: Use temp file + rename for consistency
2. **Lock Files**: Prevent concurrent modifications
3. **Backup Strategy**: Keep previous version before overwriting

### Error Handling

```json
{
  "error_states": {
    "sync_failed": {
      "retry_count": 3,
      "backoff_seconds": [60, 300, 900],
      "fallback": "queue_for_later"
    },
    "corrupt_data": {
      "action": "skip_session",
      "log_error": true
    }
  }
}
```

### Performance Considerations

- **Batch Updates**: Group multiple sessions in one sync
- **Delta Compression**: Future optimization for large deployments
- **Pagination**: Split large sync files if > 1MB

## Example Usage Flow

1. **Initial Setup**:
   ```bash
   # Generate machine UUID
   uuidgen > ~/.claude/machine_id
   
   # First full sync
   claude-sync --mode=full
   ```

2. **Regular Sync**:
   ```bash
   # Incremental sync (default)
   claude-sync
   
   # Force full sync
   claude-sync --mode=full
   ```

3. **Multi-Machine View**:
   ```bash
   # Download and merge all machine data
   claude-sync --download-all
   
   # Generate unified report
   claude-usage-tracker --source=sync
   ```

---

This format is designed to be extensible, efficient, and privacy-preserving while enabling comprehensive usage tracking across multiple machines.