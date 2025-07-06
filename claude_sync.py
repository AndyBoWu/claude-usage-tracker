#!/usr/bin/env python3
"""
claude_sync.py - iCloud synchronization for Claude Usage Tracker

This module handles syncing usage data across multiple machines using iCloud Drive.
"""

import json
import os
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ClaudeSync:
    """Handles synchronization of Claude usage data via iCloud Drive."""
    
    def __init__(self):
        """Initialize the sync manager with machine identification."""
        # Generate a unique machine identifier
        self.machine_id = self._generate_machine_id()
        
        # Define the iCloud Drive base path
        self.icloud_base = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        self.sync_dir = self.icloud_base / "ClaudeUsageTracker"
        self.data_dir = self.sync_dir / "data"
        self.processed_file = self.sync_dir / f"{self.machine_id}_processed.json"
        
    def _generate_machine_id(self) -> str:
        """Generate a unique identifier for this machine."""
        # Combine hostname and MAC address for a stable identifier
        hostname = platform.node()
        mac = uuid.getnode()
        return f"{hostname}_{mac:012x}"
    
    def is_icloud_available(self) -> bool:
        """Check if iCloud Drive is available on this system."""
        return self.icloud_base.exists() and self.icloud_base.is_dir()
    
    def initialize_sync_directory(self) -> bool:
        """Create the sync directory structure if it doesn't exist."""
        if not self.is_icloud_available():
            return False
            
        try:
            # Create directories if they don't exist
            self.sync_dir.mkdir(exist_ok=True)
            self.data_dir.mkdir(exist_ok=True)
            
            # Create a README file to explain the directory
            readme_path = self.sync_dir / "README.txt"
            if not readme_path.exists():
                readme_content = (
                    "Claude Usage Tracker Sync Directory\n"
                    "===================================\n\n"
                    "This directory contains synchronized usage data from Claude Usage Tracker.\n"
                    "Files are automatically synced across your devices via iCloud Drive.\n\n"
                    "Directory Structure:\n"
                    "- data/: Contains usage data from each machine\n"
                    "- *_processed.json: Tracks which conversations have been processed per machine\n\n"
                    "Do not manually edit these files.\n"
                )
                readme_path.write_text(readme_content)
            
            return True
            
        except Exception as e:
            print(f"Error initializing sync directory: {e}")
            return False
    
    def get_processed_conversations(self) -> Set[str]:
        """Get the set of conversation IDs that have been processed on this machine."""
        if not self.processed_file.exists():
            return set()
            
        try:
            with open(self.processed_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_conversations', []))
        except Exception as e:
            print(f"Error reading processed conversations: {e}")
            return set()
    
    def update_processed_conversations(self, conversation_ids: Set[str]) -> bool:
        """Update the list of processed conversations for this machine."""
        try:
            existing = self.get_processed_conversations()
            all_processed = existing.union(conversation_ids)
            
            data = {
                'machine_id': self.machine_id,
                'last_updated': datetime.now().isoformat(),
                'processed_conversations': sorted(list(all_processed))
            }
            
            with open(self.processed_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error updating processed conversations: {e}")
            return False
    
    def _convert_usage_list_to_dict(self, usage_list: List) -> Dict:
        """Convert a list of Usage namedtuples to the expected dictionary format.
        
        Args:
            usage_list: List of Usage namedtuples
            
        Returns:
            Dictionary with raw sessions
        """
        sessions = []
        
        for usage in usage_list:
            # Create session dict with all available fields
            session = {
                'session_id': usage.session_id if hasattr(usage, 'session_id') else None,
                'model': usage.model if hasattr(usage, 'model') else 'unknown',
                'timestamp': usage.timestamp if hasattr(usage, 'timestamp') else None,
                'input_tokens': usage.input_tokens if hasattr(usage, 'input_tokens') else 0,
                'output_tokens': usage.output_tokens if hasattr(usage, 'output_tokens') else 0,
                'cost_usd': usage.cost_usd if hasattr(usage, 'cost_usd') else 0.0,
                'project_name': usage.project_name if hasattr(usage, 'project_name') else 'unknown'
            }
            
            # Add optional fields if they exist
            if hasattr(usage, 'cache_creation_tokens'):
                session['cache_creation_tokens'] = usage.cache_creation_tokens
            if hasattr(usage, 'cache_read_tokens'):
                session['cache_read_tokens'] = usage.cache_read_tokens
            
            sessions.append(session)
        
        return {'sessions': sessions}
    
    def export_usage_data(self, usage_data, force_sync: bool = False) -> bool:
        """Export usage data to the machine-specific JSON file.
        
        Args:
            usage_data: Dictionary containing usage data or List of Usage namedtuples
            force_sync: If True, forces a sync even if data hasn't changed
        
        Returns:
            bool: True if export was successful, False otherwise
        """
        if not self.is_icloud_available():
            return False
            
        try:
            # Convert list to dict if needed
            if isinstance(usage_data, list):
                usage_data = self._convert_usage_list_to_dict(usage_data)
            elif not isinstance(usage_data, dict):
                print(f"Error: usage_data must be a list or dict, got {type(usage_data)}")
                return False
            
            # Ensure sync directory exists
            if not self.initialize_sync_directory():
                return False
            
            # Create machine-specific data file
            data_file = self.data_dir / f"{self.machine_id}_usage.json"
            
            # Check if we need to sync (if not forcing)
            if not force_sync and data_file.exists():
                try:
                    with open(data_file, 'r') as f:
                        existing_data = json.load(f)
                    # Compare usage data (excluding metadata)
                    if 'sessions' in usage_data:
                        # New format - compare sessions directly
                        if existing_data.get('sessions') == usage_data.get('sessions'):
                            return True  # No changes needed
                    else:
                        # Legacy format
                        if existing_data.get('usage_data') == usage_data:
                            return True  # No changes needed
                except Exception:
                    pass  # If we can't read existing data, proceed with export
            
            # Add metadata to the usage data
            if 'sessions' in usage_data:
                # If usage_data already has the sessions structure, use it directly
                export_data = {
                    'machine_id': self.machine_id,
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'exported_at': datetime.now().isoformat(),
                    'sessions': usage_data['sessions']
                }
            else:
                # For backward compatibility, wrap in usage_data
                export_data = {
                    'machine_id': self.machine_id,
                    'hostname': platform.node(),
                    'platform': platform.system(),
                    'exported_at': datetime.now().isoformat(),
                    'usage_data': usage_data
                }
            
            # Write the data with custom datetime handler
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(data_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=datetime_handler)
            
            return True
            
        except Exception as e:
            print(f"Error exporting usage data: {e}")
            return False
    
    def read_all_sync_data(self) -> Dict[str, Dict]:
        """Read usage data from all machines in the sync directory."""
        if not self.is_icloud_available() or not self.data_dir.exists():
            return {}
            
        all_data = {}
        
        try:
            # Read all usage data files
            for data_file in self.data_dir.glob("*_usage.json"):
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                        machine_id = data.get('machine_id', data_file.stem.replace('_usage', ''))
                        all_data[machine_id] = data
                except Exception as e:
                    print(f"Error reading {data_file}: {e}")
                    
            return all_data
            
        except Exception as e:
            print(f"Error reading sync data: {e}")
            return {}
    
    def get_all_processed_conversations(self) -> Dict[str, Set[str]]:
        """Get processed conversations from all machines."""
        if not self.is_icloud_available() or not self.sync_dir.exists():
            return {}
            
        all_processed = {}
        
        try:
            # Read all processed files
            for processed_file in self.sync_dir.glob("*_processed.json"):
                try:
                    with open(processed_file, 'r') as f:
                        data = json.load(f)
                        machine_id = data.get('machine_id', processed_file.stem.replace('_processed', ''))
                        conversations = set(data.get('processed_conversations', []))
                        all_processed[machine_id] = conversations
                except Exception as e:
                    print(f"Error reading {processed_file}: {e}")
                    
            return all_processed
            
        except Exception as e:
            print(f"Error reading processed conversations: {e}")
            return {}
    
    def merge_usage_data(self, local_data: Dict, sync_data: Dict[str, Dict]) -> Dict:
        """Merge local usage data with data from other machines."""
        # Check if we're using the new sessions format
        if 'sessions' in local_data:
            # New format - merge sessions
            merged = {'sessions': local_data['sessions'].copy()}
            seen_session_ids = {s['session_id'] for s in merged['sessions'] if s.get('session_id')}
            
            # Merge sessions from other machines
            for machine_id, machine_data in sync_data.items():
                if machine_id == self.machine_id:
                    continue  # Skip our own data
                
                # Check for sessions in the new format
                if 'sessions' in machine_data:
                    for session in machine_data['sessions']:
                        session_id = session.get('session_id')
                        if session_id and session_id not in seen_session_ids:
                            merged['sessions'].append(session)
                            seen_session_ids.add(session_id)
                        elif not session_id:
                            # Include sessions without IDs (shouldn't happen normally)
                            merged['sessions'].append(session)
                
                # Also check for sessions in usage_data for backward compatibility
                elif 'usage_data' in machine_data and 'sessions' in machine_data['usage_data']:
                    for session in machine_data['usage_data']['sessions']:
                        session_id = session.get('session_id')
                        if session_id and session_id not in seen_session_ids:
                            merged['sessions'].append(session)
                            seen_session_ids.add(session_id)
                        elif not session_id:
                            merged['sessions'].append(session)
            
            return merged
        
        # Legacy format - use the old merge logic
        merged = local_data.copy()
        
        # Merge data from other machines
        for machine_id, machine_data in sync_data.items():
            if machine_id == self.machine_id:
                continue  # Skip our own data
                
            usage = machine_data.get('usage_data', {})
            
            # Merge daily usage
            if 'daily_usage' in usage:
                if 'daily_usage' not in merged:
                    merged['daily_usage'] = {}
                    
                for date, models in usage['daily_usage'].items():
                    if date not in merged['daily_usage']:
                        merged['daily_usage'][date] = {}
                        
                    for model, stats in models.items():
                        if model not in merged['daily_usage'][date]:
                            merged['daily_usage'][date][model] = stats
                        else:
                            # Merge statistics
                            for key in ['prompt_tokens', 'completion_tokens', 'total_tokens', 
                                       'prompt_cost', 'completion_cost', 'total_cost', 'message_count']:
                                if key in stats:
                                    merged['daily_usage'][date][model][key] = (
                                        merged['daily_usage'][date][model].get(key, 0) + stats[key]
                                    )
            
            # Merge model totals
            if 'model_totals' in usage:
                if 'model_totals' not in merged:
                    merged['model_totals'] = {}
                    
                for model, stats in usage['model_totals'].items():
                    if model not in merged['model_totals']:
                        merged['model_totals'][model] = stats
                    else:
                        # Merge statistics
                        for key in ['prompt_tokens', 'completion_tokens', 'total_tokens', 
                                   'prompt_cost', 'completion_cost', 'total_cost', 'message_count']:
                            if key in stats:
                                merged['model_totals'][model][key] = (
                                    merged['model_totals'][model].get(key, 0) + stats[key]
                                )
            
            # Merge conversation details if present
            if 'conversations' in usage and 'conversations' in merged:
                # Avoid duplicates by using conversation ID as key
                for conv in usage['conversations']:
                    conv_id = conv.get('id')
                    if conv_id and not any(c.get('id') == conv_id for c in merged['conversations']):
                        merged['conversations'].append(conv)
        
        return merged
    
    def get_sync_status(self) -> Dict[str, any]:
        """Get the current synchronization status."""
        status = {
            'icloud_available': self.is_icloud_available(),
            'machine_id': self.machine_id,
            'hostname': platform.node(),
            'sync_directory': str(self.sync_dir) if self.is_icloud_available() else None,
            'machines_synced': [],
            'total_conversations_synced': 0
        }
        
        if status['icloud_available']:
            # Get info about all synced machines
            all_processed = self.get_all_processed_conversations()
            all_data = self.read_all_sync_data()
            
            for machine_id in set(list(all_processed.keys()) + list(all_data.keys())):
                machine_info = {
                    'machine_id': machine_id,
                    'is_current': machine_id == self.machine_id,
                    'conversations_processed': len(all_processed.get(machine_id, set())),
                    'has_usage_data': machine_id in all_data
                }
                
                if machine_id in all_data:
                    data = all_data[machine_id]
                    machine_info['hostname'] = data.get('hostname', 'Unknown')
                    machine_info['platform'] = data.get('platform', 'Unknown')
                    machine_info['last_export'] = data.get('exported_at', 'Unknown')
                
                status['machines_synced'].append(machine_info)
            
            # Calculate total unique conversations
            all_conversations = set()
            for conversations in all_processed.values():
                all_conversations.update(conversations)
            status['total_conversations_synced'] = len(all_conversations)
        
        return status
    
    def read_reconciled_data(self) -> List[Tuple]:
        """Read the most recent reconciled data file and convert to Usage namedtuples.
        
        Returns:
            List of Usage namedtuples containing reconciled session data
        """
        # Import Usage namedtuple from main tracker
        from collections import namedtuple
        Usage = namedtuple('Usage', ['input_tokens', 'output_tokens', 'cache_creation_tokens', 
                                     'cache_read_tokens', 'cost_usd', 'model', 'timestamp', 
                                     'project_name', 'session_id'])
        
        usage_list = []
        
        if not self.is_icloud_available() or not self.sync_dir.exists():
            return usage_list
        
        try:
            # Find the most recent reconciled data file
            reconciled_files = sorted(self.sync_dir.glob('reconciled_sessions_*.json'), reverse=True)
            
            if not reconciled_files:
                print("No reconciled data files found")
                return usage_list
            
            # Read the most recent file
            latest_file = reconciled_files[0]
            print(f"Reading reconciled data from: {latest_file.name}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Extract sessions from the reconciled data
            sessions = data.get('sessions', [])
            
            # Convert each session to a Usage namedtuple
            for session in sessions:
                try:
                    # Extract required fields with defaults
                    input_tokens = session.get('input_tokens', 0)
                    output_tokens = session.get('output_tokens', 0)
                    cache_creation_tokens = session.get('cache_creation_tokens', 0)
                    cache_read_tokens = session.get('cache_read_tokens', 0)
                    cost_usd = session.get('total_cost', 0.0)
                    model = session.get('model', 'unknown')
                    
                    # Parse timestamp string to datetime object
                    timestamp_str = session.get('timestamp', '')
                    timestamp = None
                    if timestamp_str:
                        try:
                            # Handle ISO format with Z suffix
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            # If parsing fails, leave as None
                            timestamp = None
                    
                    project_name = session.get('project', session.get('project_name', 'unknown'))
                    session_id = session.get('session_id', '')
                    
                    # Create Usage namedtuple
                    usage = Usage(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_creation_tokens=cache_creation_tokens,
                        cache_read_tokens=cache_read_tokens,
                        cost_usd=cost_usd,
                        model=model,
                        timestamp=timestamp,
                        project_name=project_name,
                        session_id=session_id
                    )
                    
                    usage_list.append(usage)
                    
                except Exception as e:
                    print(f"Error converting session to Usage: {e}")
                    continue
            
            print(f"Successfully loaded {len(usage_list)} sessions from reconciled data")
            return usage_list
            
        except Exception as e:
            print(f"Error reading reconciled data: {e}")
            return usage_list


# Standalone functions for easier import and use
def get_sync_status() -> Dict[str, any]:
    """Get the current synchronization status.
    
    Returns:
        Dictionary containing sync status information
    """
    sync = ClaudeSync()
    return sync.get_sync_status()


def export_usage_data(usage_data, force_sync: bool = False) -> bool:
    """Export usage data to iCloud sync.
    
    Args:
        usage_data: Dictionary containing usage data or List of Usage namedtuples
        force_sync: If True, forces a sync even if data hasn't changed
    
    Returns:
        bool: True if export was successful, False otherwise
    """
    sync = ClaudeSync()
    return sync.export_usage_data(usage_data, force_sync=force_sync)


def is_icloud_available() -> bool:
    """Check if iCloud Drive is available.
    
    Returns:
        bool: True if iCloud Drive is available, False otherwise
    """
    sync = ClaudeSync()
    return sync.is_icloud_available()


def initialize_sync_directory() -> bool:
    """Initialize the sync directory structure.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    sync = ClaudeSync()
    return sync.initialize_sync_directory()


def read_reconciled_data() -> List[Tuple]:
    """Read the most recent reconciled data file.
    
    Returns:
        List of Usage namedtuples containing reconciled session data
    """
    sync = ClaudeSync()
    return sync.read_reconciled_data()


# Example usage and testing
if __name__ == "__main__":
    sync = ClaudeSync()
    
    print(f"Machine ID: {sync.machine_id}")
    print(f"iCloud Available: {sync.is_icloud_available()}")
    
    if sync.is_icloud_available():
        print(f"Sync Directory: {sync.sync_dir}")
        
        # Initialize sync directory
        if sync.initialize_sync_directory():
            print("Sync directory initialized successfully")
        
        # Get sync status
        status = sync.get_sync_status()
        print("\nSync Status:")
        # Use the same datetime handler for printing status
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        print(json.dumps(status, indent=2, default=datetime_handler))
        
        # Test data export with new session format
        test_data = {
            'sessions': [
                {
                    'session_id': 'test-session-123',
                    'model': 'claude-3-5-sonnet-20241022',
                    'timestamp': datetime.now().isoformat(),
                    'input_tokens': 1000,
                    'output_tokens': 500,
                    'cost_usd': 0.015,
                    'project_name': 'test-project'
                }
            ]
        }
        
        if sync.export_usage_data(test_data):
            print("\nTest data exported successfully")