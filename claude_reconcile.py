#!/usr/bin/env python3
"""
Claude Usage Data Reconciliation Tool

Merges usage data from multiple machines synced via iCloud, handling duplicates
and conflicts intelligently.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UsageDataReconciler:
    """Reconciles Claude usage data from multiple machines."""
    
    def __init__(self, sync_dir: Path, output_dir: Optional[Path] = None):
        self.sync_dir = sync_dir
        self.output_dir = output_dir or sync_dir
        self.sessions_by_id: Dict[str, List[Dict]] = defaultdict(list)
        self.machine_stats: Dict[str, Dict] = {}
        self.conflicts: List[Dict] = []
        self.errors: List[Dict] = []
        
    def reconcile(self) -> Dict[str, Any]:
        """Main reconciliation process."""
        logger.info(f"Starting reconciliation from {self.sync_dir}")
        
        # Step 1: Discover and load all JSON files
        json_files = self._discover_json_files()
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Step 2: Load and validate data from each file
        for json_file in json_files:
            self._load_machine_data(json_file)
        
        # Step 3: Reconcile duplicate sessions
        reconciled_sessions = self._reconcile_sessions()
        
        # Step 4: Generate consolidated report
        report = self._generate_report(reconciled_sessions)
        
        # Step 5: Save reconciled data
        self._save_reconciled_data(reconciled_sessions, report)
        
        return report
    
    def _discover_json_files(self) -> List[Path]:
        """Find all machine-specific JSON files in the sync directory."""
        json_files = []
        
        if not self.sync_dir.exists():
            logger.error(f"Sync directory does not exist: {self.sync_dir}")
            return json_files
        
        # Look for JSON files matching expected patterns
        patterns = [
            "claude_usage_*.json",
            "usage_data_*.json",
            "*_claude_usage.json",
            "*_usage.json",
            "*.json"
        ]
        
        for pattern in patterns:
            json_files.extend(self.sync_dir.glob(pattern))
        
        # Also check subdirectories
        for subdir in self.sync_dir.iterdir():
            if subdir.is_dir():
                for pattern in patterns:
                    json_files.extend(subdir.glob(pattern))
        
        return sorted(set(json_files))
    
    def _load_machine_data(self, json_file: Path) -> None:
        """Load and validate data from a single machine's JSON file."""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract machine identifier from filename or data
            machine_id = self._extract_machine_id(json_file, data)
            
            # Validate data structure
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data)}")
            
            # Extract sessions/usage data
            sessions = self._extract_sessions(data)
            
            # Track statistics per machine
            self.machine_stats[machine_id] = {
                'file': str(json_file),
                'session_count': len(sessions),
                'last_modified': datetime.fromtimestamp(
                    json_file.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                'total_cost': sum(s.get('total_cost', 0) for s in sessions),
                'total_tokens': sum(
                    s.get('input_tokens', 0) + s.get('output_tokens', 0) 
                    for s in sessions
                )
            }
            
            # Store sessions with machine info
            for session in sessions:
                session['_machine_id'] = machine_id
                session['_source_file'] = str(json_file)
                session['_file_modified'] = json_file.stat().st_mtime
                
                session_id = session.get('session_id') or session.get('id')
                if session_id:
                    self.sessions_by_id[session_id].append(session)
                else:
                    logger.warning(f"Session without ID in {json_file}: {session}")
            
            logger.info(f"Loaded {len(sessions)} sessions from {machine_id}")
            
        except json.JSONDecodeError as e:
            error = {
                'file': str(json_file),
                'error': f"JSON decode error: {e}",
                'type': 'corrupt_file'
            }
            self.errors.append(error)
            logger.error(f"Failed to parse {json_file}: {e}")
        except Exception as e:
            error = {
                'file': str(json_file),
                'error': str(e),
                'type': 'unknown_error'
            }
            self.errors.append(error)
            logger.error(f"Error loading {json_file}: {e}")
    
    def _extract_machine_id(self, json_file: Path, data: Dict) -> str:
        """Extract machine identifier from filename or data."""
        # Try to get from data first
        if 'machine_id' in data:
            return data['machine_id']
        if 'hostname' in data:
            return data['hostname']
        
        # Extract from filename
        filename = json_file.stem
        parts = filename.split('_')
        
        # Common patterns: claude_usage_MACHINE, usage_data_MACHINE
        if len(parts) >= 3:
            return '_'.join(parts[2:])
        
        # Fallback to parent directory name
        if json_file.parent != self.sync_dir:
            return json_file.parent.name
        
        # Last resort: use file hash
        return f"unknown_{hash(str(json_file)) % 10000}"
    
    def _extract_sessions(self, data: Dict) -> List[Dict]:
        """Extract session data from various possible formats."""
        sessions = []
        
        # Check common data structures
        if 'sessions' in data:
            sessions = data['sessions']
        elif 'usage_data' in data:
            sessions = data['usage_data']
        elif 'conversations' in data:
            sessions = data['conversations']
        elif 'data' in data and isinstance(data['data'], list):
            sessions = data['data']
        elif isinstance(data, list):
            sessions = data
        else:
            # Try to find any list-like structure
            for key, value in data.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    sessions = value
                    break
        
        # Ensure sessions is a list
        if not isinstance(sessions, list):
            sessions = [sessions]
        
        # Validate and normalize session data
        normalized_sessions = []
        for session in sessions:
            if isinstance(session, dict):
                normalized = self._normalize_session(session)
                if normalized:
                    normalized_sessions.append(normalized)
        
        return normalized_sessions
    
    def _normalize_session(self, session: Dict) -> Optional[Dict]:
        """Normalize session data to a common format."""
        normalized = {}
        
        # Map various field names to standard names
        id_fields = ['session_id', 'id', 'conversation_id', 'uuid']
        for field in id_fields:
            if field in session:
                normalized['session_id'] = str(session[field])
                break
        
        if 'session_id' not in normalized:
            return None  # Skip sessions without IDs
        
        # Timestamp fields
        timestamp_fields = ['timestamp', 'created_at', 'date', 'start_time']
        for field in timestamp_fields:
            if field in session:
                normalized['timestamp'] = self._parse_timestamp(session[field])
                break
        
        # Token fields
        normalized['input_tokens'] = (
            session.get('input_tokens', 0) or 
            session.get('prompt_tokens', 0) or 
            session.get('inputs', 0) or 0
        )
        normalized['output_tokens'] = (
            session.get('output_tokens', 0) or 
            session.get('completion_tokens', 0) or 
            session.get('outputs', 0) or 0
        )
        
        # Cost fields
        normalized['total_cost'] = (
            session.get('total_cost', 0) or 
            session.get('cost', 0) or 
            session.get('price', 0) or 0
        )
        
        # Model information
        normalized['model'] = (
            session.get('model') or 
            session.get('model_name') or 
            session.get('model_id') or 
            'unknown'
        )
        
        # Project/context information
        normalized['project'] = session.get('project', session.get('project_name'))
        normalized['title'] = session.get('title', session.get('conversation_title'))
        
        # Preserve any additional fields
        for key, value in session.items():
            if key not in normalized and not key.startswith('_'):
                normalized[key] = value
        
        return normalized
    
    def _parse_timestamp(self, timestamp: Any) -> str:
        """Parse various timestamp formats to ISO format."""
        if isinstance(timestamp, str):
            # Already in ISO format
            if 'T' in timestamp:
                return timestamp
            # Try parsing common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    return dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    continue
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.isoformat()
        
        # Fallback
        return datetime.now(timezone.utc).isoformat()
    
    def _reconcile_sessions(self) -> Dict[str, Dict]:
        """Reconcile duplicate sessions from multiple machines."""
        reconciled = {}
        
        for session_id, duplicates in self.sessions_by_id.items():
            if len(duplicates) == 1:
                # No conflict
                reconciled[session_id] = duplicates[0]
            else:
                # Conflict resolution needed
                resolved = self._resolve_conflict(session_id, duplicates)
                reconciled[session_id] = resolved
        
        logger.info(f"Reconciled {len(reconciled)} unique sessions")
        logger.info(f"Resolved {len(self.conflicts)} conflicts")
        
        return reconciled
    
    def _resolve_conflict(self, session_id: str, duplicates: List[Dict]) -> Dict:
        """Resolve conflicts between duplicate sessions."""
        # Track conflict for reporting
        conflict = {
            'session_id': session_id,
            'duplicates': len(duplicates),
            'machines': list(set(d['_machine_id'] for d in duplicates)),
            'resolution': None
        }
        
        # Sort by file modification time (most recent first)
        duplicates.sort(key=lambda x: x['_file_modified'], reverse=True)
        
        # Check if all duplicates have the same content
        if self._are_duplicates_identical(duplicates):
            conflict['resolution'] = 'identical_content'
            self.conflicts.append(conflict)
            return duplicates[0]
        
        # Use the most complete record
        best_duplicate = None
        max_fields = 0
        max_tokens = 0
        
        for dup in duplicates:
            # Count non-empty fields
            field_count = sum(1 for v in dup.values() if v and not str(v).startswith('_'))
            total_tokens = dup.get('input_tokens', 0) + dup.get('output_tokens', 0)
            
            # Prefer records with more fields or higher token counts
            if field_count > max_fields or (field_count == max_fields and total_tokens > max_tokens):
                max_fields = field_count
                max_tokens = total_tokens
                best_duplicate = dup
        
        if best_duplicate:
            conflict['resolution'] = 'most_complete_record'
            conflict['selected_machine'] = best_duplicate['_machine_id']
            self.conflicts.append(conflict)
            return best_duplicate
        
        # Fallback to most recent
        conflict['resolution'] = 'most_recent'
        conflict['selected_machine'] = duplicates[0]['_machine_id']
        self.conflicts.append(conflict)
        return duplicates[0]
    
    def _are_duplicates_identical(self, duplicates: List[Dict]) -> bool:
        """Check if duplicate sessions have identical content."""
        if len(duplicates) < 2:
            return True
        
        # Compare key fields
        key_fields = ['input_tokens', 'output_tokens', 'total_cost', 'model', 'timestamp']
        
        first = duplicates[0]
        for dup in duplicates[1:]:
            for field in key_fields:
                if first.get(field) != dup.get(field):
                    return False
        
        return True
    
    def _generate_report(self, sessions: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate comprehensive reconciliation report."""
        # Calculate aggregate statistics
        total_sessions = len(sessions)
        total_input_tokens = sum(s.get('input_tokens', 0) for s in sessions.values())
        total_output_tokens = sum(s.get('output_tokens', 0) for s in sessions.values())
        total_cost = sum(s.get('total_cost', 0) for s in sessions.values())
        
        # Group by model
        model_stats = defaultdict(lambda: {
            'sessions': 0, 'input_tokens': 0, 'output_tokens': 0, 'cost': 0
        })
        
        for session in sessions.values():
            model = session.get('model', 'unknown')
            model_stats[model]['sessions'] += 1
            model_stats[model]['input_tokens'] += session.get('input_tokens', 0)
            model_stats[model]['output_tokens'] += session.get('output_tokens', 0)
            model_stats[model]['cost'] += session.get('total_cost', 0)
        
        # Time-based analysis
        timestamps = []
        for session in sessions.values():
            ts = session.get('timestamp')
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                except:
                    pass
        
        if timestamps:
            timestamps.sort()
            date_range = {
                'earliest': timestamps[0].isoformat(),
                'latest': timestamps[-1].isoformat(),
                'days_covered': (timestamps[-1] - timestamps[0]).days + 1
            }
        else:
            date_range = {'earliest': None, 'latest': None, 'days_covered': 0}
        
        report = {
            'reconciliation_timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_sessions': total_sessions,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'total_cost': round(total_cost, 4),
                'unique_models': len(model_stats),
                'date_range': date_range
            },
            'machine_stats': self.machine_stats,
            'model_breakdown': dict(model_stats),
            'conflicts': {
                'total': len(self.conflicts),
                'by_resolution': self._group_conflicts_by_resolution(),
                'details': self.conflicts[:10]  # First 10 conflicts
            },
            'errors': {
                'total': len(self.errors),
                'by_type': self._group_errors_by_type(),
                'details': self.errors
            }
        }
        
        return report
    
    def _group_conflicts_by_resolution(self) -> Dict[str, int]:
        """Group conflicts by resolution method."""
        by_resolution = defaultdict(int)
        for conflict in self.conflicts:
            by_resolution[conflict['resolution']] += 1
        return dict(by_resolution)
    
    def _group_errors_by_type(self) -> Dict[str, int]:
        """Group errors by type."""
        by_type = defaultdict(int)
        for error in self.errors:
            by_type[error['type']] += 1
        return dict(by_type)
    
    def _save_reconciled_data(self, sessions: Dict[str, Dict], report: Dict[str, Any]) -> None:
        """Save reconciled data and report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save reconciled sessions
        sessions_file = self.output_dir / f'reconciled_sessions_{timestamp}.json'
        with open(sessions_file, 'w') as f:
            json.dump({
                'metadata': {
                    'reconciliation_timestamp': report['reconciliation_timestamp'],
                    'total_sessions': len(sessions),
                    'source_machines': list(self.machine_stats.keys())
                },
                'sessions': list(sessions.values())
            }, f, indent=2)
        
        logger.info(f"Saved reconciled sessions to {sessions_file}")
        
        # Save detailed report
        report_file = self.output_dir / f'reconciliation_report_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved reconciliation report to {report_file}")
        
        # Save human-readable summary
        summary_file = self.output_dir / f'reconciliation_summary_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write(self._format_summary(report))
        
        logger.info(f"Saved summary to {summary_file}")
    
    def _format_summary(self, report: Dict[str, Any]) -> str:
        """Format a human-readable summary of the reconciliation."""
        lines = []
        lines.append("=" * 60)
        lines.append("Claude Usage Data Reconciliation Summary")
        lines.append("=" * 60)
        lines.append(f"Generated: {report['reconciliation_timestamp']}")
        lines.append("")
        
        # Overall statistics
        summary = report['summary']
        lines.append("OVERALL STATISTICS:")
        lines.append(f"  Total Sessions: {summary['total_sessions']:,}")
        lines.append(f"  Total Input Tokens: {summary['total_input_tokens']:,}")
        lines.append(f"  Total Output Tokens: {summary['total_output_tokens']:,}")
        lines.append(f"  Total Tokens: {summary['total_tokens']:,}")
        lines.append(f"  Total Cost: ${summary['total_cost']:.2f}")
        
        if summary['date_range']['earliest']:
            lines.append(f"  Date Range: {summary['date_range']['earliest'][:10]} to {summary['date_range']['latest'][:10]}")
            lines.append(f"  Days Covered: {summary['date_range']['days_covered']}")
        lines.append("")
        
        # Machine statistics
        lines.append("MACHINE STATISTICS:")
        for machine_id, stats in report['machine_stats'].items():
            lines.append(f"  {machine_id}:")
            lines.append(f"    Sessions: {stats['session_count']:,}")
            lines.append(f"    Total Cost: ${stats['total_cost']:.2f}")
            lines.append(f"    Last Modified: {stats['last_modified'][:19]}")
        lines.append("")
        
        # Model breakdown
        lines.append("MODEL BREAKDOWN:")
        for model, stats in report['model_breakdown'].items():
            lines.append(f"  {model}:")
            lines.append(f"    Sessions: {stats['sessions']:,}")
            lines.append(f"    Input Tokens: {stats['input_tokens']:,}")
            lines.append(f"    Output Tokens: {stats['output_tokens']:,}")
            lines.append(f"    Cost: ${stats['cost']:.2f}")
        lines.append("")
        
        # Conflicts
        if report['conflicts']['total'] > 0:
            lines.append("CONFLICT RESOLUTION:")
            lines.append(f"  Total Conflicts: {report['conflicts']['total']}")
            lines.append("  Resolution Methods:")
            for method, count in report['conflicts']['by_resolution'].items():
                lines.append(f"    {method}: {count}")
        lines.append("")
        
        # Errors
        if report['errors']['total'] > 0:
            lines.append("ERRORS:")
            lines.append(f"  Total Errors: {report['errors']['total']}")
            lines.append("  Error Types:")
            for error_type, count in report['errors']['by_type'].items():
                lines.append(f"    {error_type}: {count}")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Reconcile Claude usage data from multiple machines'
    )
    parser.add_argument(
        '--sync-dir',
        type=Path,
        help='iCloud sync directory containing machine-specific JSON files',
        default=Path.home() / 'Library' / 'Mobile Documents' / 'com~apple~CloudDocs' / 'Claude Usage Data'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Directory to save reconciled data (defaults to sync-dir)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform reconciliation but do not save files'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create reconciler
    reconciler = UsageDataReconciler(args.sync_dir, args.output_dir)
    
    try:
        # Run reconciliation
        report = reconciler.reconcile()
        
        # Print summary
        print("\nReconciliation complete!")
        print(f"Total sessions reconciled: {report['summary']['total_sessions']:,}")
        print(f"Total cost: ${report['summary']['total_cost']:.2f}")
        print(f"Conflicts resolved: {report['conflicts']['total']}")
        print(f"Errors encountered: {report['errors']['total']}")
        
        if args.dry_run:
            print("\n(Dry run - no files were saved)")
        
    except Exception as e:
        logger.error(f"Reconciliation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()