#!/usr/bin/env python3
"""
Test script for Claude Usage Tracker sync functionality.

Tests the sync and reconciliation features with sample data,
including error handling for when iCloud is not available.
"""

import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import platform
import uuid

# Import the necessary modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_usage_tracker import Usage, ClaudeUsageTracker


class SyncTester:
    """Test harness for Claude sync functionality."""
    
    def __init__(self, use_temp_dir: bool = True):
        """Initialize the sync tester."""
        self.use_temp_dir = use_temp_dir
        self.temp_dir = None
        self.original_home = None
        
        # Check if we're on macOS
        self.is_macos = platform.system() == 'Darwin'
        
        # Check if iCloud is available
        self.icloud_path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        self.icloud_available = self.is_macos and self.icloud_path.exists()
        
        print(f"Platform: {platform.system()}")
        print(f"iCloud available: {self.icloud_available}")
        
    def setup_test_environment(self):
        """Set up a test environment."""
        if self.use_temp_dir:
            # Create temporary directory structure
            self.temp_dir = tempfile.mkdtemp(prefix="claude_sync_test_")
            self.test_home = Path(self.temp_dir) / "home"
            self.test_home.mkdir()
            
            # Create fake iCloud structure if testing locally
            if not self.icloud_available:
                self.fake_icloud = self.test_home / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
                self.fake_icloud.mkdir(parents=True)
            
            print(f"Test environment created at: {self.temp_dir}")
        
    def cleanup_test_environment(self):
        """Clean up the test environment."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"Test environment cleaned up: {self.temp_dir}")
    
    def create_sample_usage_data(self, machine_suffix: str = "test") -> List[Usage]:
        """Create a sample set of usage data for testing."""
        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        
        usage_data = []
        models = [
            'claude-sonnet-4-20250514',
            'claude-opus-4-20250514',
            'claude-3-5-sonnet-20241022'
        ]
        
        # Create 20 sample usage records over 7 days
        for i in range(20):
            timestamp = base_time + timedelta(hours=i * 8)
            model = models[i % len(models)]
            
            # Vary the token counts
            input_tokens = 500 + (i * 100)
            output_tokens = 300 + (i * 50)
            cache_creation = 100 if i % 3 == 0 else 0
            cache_read = 200 if i % 2 == 0 else 0
            
            # Calculate cost (simplified)
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
            
            usage = Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_tokens=cache_creation,
                cache_read_tokens=cache_read,
                cost_usd=cost,
                model=model,
                timestamp=timestamp,
                project_name=f"test_project_{i % 3}",
                session_id=f"{machine_suffix}_session_{i:04d}"
            )
            
            usage_data.append(usage)
        
        return usage_data
    
    def test_export_to_icloud(self, usage_data: List[Usage]) -> bool:
        """Test exporting usage data to iCloud."""
        print("\n=== Testing Export to iCloud ===")
        
        try:
            # Import sync module
            from claude_sync import export_usage_data, is_icloud_available, initialize_sync_directory
            
            # Check iCloud availability
            if not is_icloud_available():
                print("iCloud is not available on this system")
                print("This is expected on non-macOS systems or when iCloud Drive is not configured")
                return False
            
            # Initialize sync directory
            print("Initializing sync directory...")
            if not initialize_sync_directory():
                print("Failed to initialize sync directory")
                return False
            
            # Export data
            print(f"Exporting {len(usage_data)} usage records...")
            success = export_usage_data(usage_data, force_sync=True)
            
            if success:
                print("✅ Successfully exported usage data to iCloud")
            else:
                print("❌ Failed to export usage data")
            
            return success
            
        except ImportError as e:
            print(f"Error: claude_sync module not found: {e}")
            return False
        except Exception as e:
            print(f"Error during export: {e}")
            return False
    
    def test_read_synced_data(self) -> Optional[List[Usage]]:
        """Test reading back synced data from iCloud."""
        print("\n=== Testing Read from iCloud ===")
        
        try:
            from claude_sync import read_reconciled_data, get_sync_status
            
            # Get sync status first
            status = get_sync_status()
            print(f"Synced machines: {status.get('synced_machines', 0)}")
            print(f"Total conversations: {status.get('total_conversations', 0)}")
            
            # Try to read reconciled data
            synced_data = read_reconciled_data()
            
            if synced_data:
                print(f"✅ Successfully read {len(synced_data)} records from sync")
                return synced_data
            else:
                print("No synced data found")
                return None
                
        except ImportError as e:
            print(f"Error: claude_sync module not found: {e}")
            return None
        except Exception as e:
            print(f"Error reading synced data: {e}")
            return None
    
    def test_reconciliation(self, machine_count: int = 3) -> bool:
        """Test the reconciliation process with data from multiple machines."""
        print(f"\n=== Testing Reconciliation ({machine_count} machines) ===")
        
        try:
            # Create sample data for multiple machines
            all_machine_data = {}
            
            for i in range(machine_count):
                machine_id = f"test_machine_{i}"
                usage_data = self.create_sample_usage_data(machine_suffix=machine_id)
                
                # Add some duplicates between machines
                if i > 0:
                    # Copy some sessions from previous machine to create conflicts
                    prev_data = all_machine_data[f"test_machine_{i-1}"]
                    for j in range(3):  # Copy 3 sessions
                        duplicate = prev_data[j]
                        # Modify slightly to create conflicts
                        modified = Usage(
                            input_tokens=duplicate.input_tokens + 10,
                            output_tokens=duplicate.output_tokens,
                            cache_creation_tokens=duplicate.cache_creation_tokens,
                            cache_read_tokens=duplicate.cache_read_tokens,
                            cost_usd=duplicate.cost_usd * 1.1,
                            model=duplicate.model,
                            timestamp=duplicate.timestamp,
                            project_name=duplicate.project_name,
                            session_id=duplicate.session_id  # Same ID = conflict
                        )
                        usage_data[j] = modified
                
                all_machine_data[machine_id] = usage_data
            
            # Simulate saving data from each machine
            if self.use_temp_dir and not self.icloud_available:
                sync_dir = self.fake_icloud / "ClaudeUsageTracker" / "data"
                sync_dir.mkdir(parents=True, exist_ok=True)
                
                for machine_id, usage_data in all_machine_data.items():
                    # Convert Usage objects to dictionaries
                    data_dicts = []
                    for usage in usage_data:
                        data_dict = {
                            'session_id': usage.session_id,
                            'input_tokens': usage.input_tokens,
                            'output_tokens': usage.output_tokens,
                            'cache_creation_tokens': usage.cache_creation_tokens,
                            'cache_read_tokens': usage.cache_read_tokens,
                            'total_cost': usage.cost_usd,
                            'model': usage.model,
                            'timestamp': usage.timestamp.isoformat() if usage.timestamp else None,
                            'project': usage.project_name
                        }
                        data_dicts.append(data_dict)
                    
                    # Save to file
                    export_data = {
                        'machine_id': machine_id,
                        'hostname': f"{machine_id}_host",
                        'platform': platform.system(),
                        'exported_at': datetime.now().isoformat(),
                        'usage_data': data_dicts
                    }
                    
                    output_file = sync_dir / f"{machine_id}_usage.json"
                    with open(output_file, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    print(f"Saved test data for {machine_id} to {output_file}")
            
            # Run reconciliation
            print("\nRunning reconciliation process...")
            
            # Import and use the reconciler directly
            from claude_reconcile import UsageDataReconciler
            
            if self.use_temp_dir and not self.icloud_available:
                reconciler = UsageDataReconciler(
                    sync_dir=self.fake_icloud / "ClaudeUsageTracker",
                    output_dir=self.fake_icloud / "ClaudeUsageTracker"
                )
            else:
                sync_base = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "ClaudeUsageTracker"
                reconciler = UsageDataReconciler(sync_dir=sync_base)
            
            report = reconciler.reconcile()
            
            # Analyze results
            print(f"\nReconciliation Results:")
            print(f"  Total sessions: {report['summary']['total_sessions']}")
            print(f"  Total conflicts: {report['conflicts']['total']}")
            print(f"  Total errors: {report['errors']['total']}")
            print(f"  Machines processed: {len(report['machine_stats'])}")
            
            # Show conflict resolution details
            if report['conflicts']['total'] > 0:
                print(f"\nConflict Resolution Methods:")
                for method, count in report['conflicts']['by_resolution'].items():
                    print(f"  {method}: {count}")
            
            return report['summary']['total_sessions'] > 0
            
        except Exception as e:
            print(f"Error during reconciliation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_data_integrity(self, original_data: List[Usage], synced_data: List[Usage]) -> bool:
        """Verify that data integrity is maintained through sync/reconciliation."""
        print("\n=== Verifying Data Integrity ===")
        
        if not synced_data:
            print("No synced data to verify")
            return False
        
        # Create lookup dictionaries
        original_by_id = {u.session_id: u for u in original_data}
        synced_by_id = {u.session_id: u for u in synced_data}
        
        # Check for missing sessions
        missing_sessions = set(original_by_id.keys()) - set(synced_by_id.keys())
        if missing_sessions:
            print(f"❌ Missing {len(missing_sessions)} sessions after sync:")
            for session_id in list(missing_sessions)[:5]:
                print(f"    - {session_id}")
            return False
        
        # Check for data corruption
        corrupted = 0
        for session_id, original in original_by_id.items():
            if session_id in synced_by_id:
                synced = synced_by_id[session_id]
                
                # Allow small differences due to reconciliation
                if abs(original.cost_usd - synced.cost_usd) > 0.01:
                    corrupted += 1
                    print(f"Cost mismatch for {session_id}: {original.cost_usd} vs {synced.cost_usd}")
        
        if corrupted > 0:
            print(f"❌ Found {corrupted} sessions with data corruption")
            return False
        
        print("✅ Data integrity verified successfully")
        return True
    
    def run_all_tests(self):
        """Run all sync tests."""
        print("=" * 60)
        print("Claude Usage Tracker Sync Test Suite")
        print("=" * 60)
        
        try:
            # Set up test environment
            self.setup_test_environment()
            
            # Test 1: Create sample data
            print("\n1. Creating sample usage data...")
            sample_data = self.create_sample_usage_data(machine_suffix="test_main")
            print(f"   Created {len(sample_data)} sample usage records")
            
            # Test 2: Export to iCloud
            export_success = False
            if self.icloud_available or self.use_temp_dir:
                export_success = self.test_export_to_icloud(sample_data)
            else:
                print("\n2. Skipping iCloud export test (iCloud not available)")
            
            # Test 3: Read back synced data
            synced_data = None
            if export_success:
                synced_data = self.test_read_synced_data()
            else:
                print("\n3. Skipping sync read test (export failed or not attempted)")
            
            # Test 4: Test reconciliation with multiple machines
            reconcile_success = self.test_reconciliation(machine_count=3)
            
            # Test 5: Verify data integrity
            if synced_data:
                integrity_verified = self.verify_data_integrity(sample_data, synced_data)
            else:
                print("\n5. Skipping integrity verification (no synced data)")
                integrity_verified = False
            
            # Summary
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            print(f"Platform: {platform.system()}")
            print(f"iCloud Available: {self.icloud_available}")
            print(f"Export Test: {'✅ Passed' if export_success else '❌ Failed/Skipped'}")
            print(f"Read Test: {'✅ Passed' if synced_data else '❌ Failed/Skipped'}")
            print(f"Reconciliation Test: {'✅ Passed' if reconcile_success else '❌ Failed'}")
            print(f"Integrity Test: {'✅ Passed' if integrity_verified else '❌ Failed/Skipped'}")
            
        finally:
            # Clean up
            self.cleanup_test_environment()


def main():
    """Main entry point for sync tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Claude Usage Tracker sync functionality')
    parser.add_argument('--no-temp', action='store_true', 
                       help='Use real iCloud directory instead of temp directory')
    parser.add_argument('--keep-temp', action='store_true',
                       help='Do not clean up temporary test files')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = SyncTester(use_temp_dir=not args.no_temp)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not args.keep_temp:
            tester.cleanup_test_environment()


if __name__ == '__main__':
    main()