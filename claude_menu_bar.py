#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS
Shows real-time Claude usage statistics in the macOS menu bar
"""

import rumps
import subprocess
import json
import os
import re
from datetime import datetime
import threading
import time

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Claude: Loading...", quit_button=None)
        # Clear any default menu items first
        self.menu.clear()
        self.menu = [
            "Today's Requests: Loading...",
            "Today's Cost: Loading...",
            None,  # Separator
            "30-Day Average: Loading...",
            "Monthly Total: Loading...",
            None,  # Separator
            "Sync to iCloud",
            "Reconcile All Macs",
            "View Combined Stats",
            None,  # Separator
            "Sync Status",
            None,  # Separator
            "Refresh Now",
            "Auto-refresh: ON",
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.auto_refresh = True
        self.refresh_interval = 30  # 30 seconds
        self.script_path = os.path.join(os.path.dirname(__file__), "claude_usage_tracker.py")
        
        # Start auto-refresh thread
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        # Initial refresh
        self.refresh_stats()
    
    def auto_refresh_loop(self):
        """Background thread for auto-refreshing stats"""
        while True:
            if self.auto_refresh:
                self.refresh_stats()
            time.sleep(self.refresh_interval)
    
    def parse_usage_output(self, output):
        """Parse the CLI output to extract key metrics"""
        stats = {
            'total_requests': 'N/A',
            'total_cost': 'N/A',
            'daily_avg': 'N/A',
            'monthly_est': 'N/A',
            'today_requests': 'N/A',
            'today_cost': 'N/A'
        }
        
        # Parse total requests
        requests_match = re.search(r'Total requests:\s*([\d,]+)', output)
        if requests_match:
            stats['total_requests'] = requests_match.group(1)
        
        # Parse API equivalent cost
        cost_match = re.search(r'API equivalent:\s*\$([\d,]+\.?\d*)', output)
        if cost_match:
            stats['total_cost'] = f"${cost_match.group(1)}"
        
        # Parse daily average
        daily_match = re.search(r'Daily average:\s*\$([\d,]+\.?\d*)', output)
        if daily_match:
            stats['daily_avg'] = f"${daily_match.group(1)}"
        
        # Parse monthly estimate
        monthly_match = re.search(r'Monthly estimate:\s*\$([\d,]+\.?\d*)', output)
        if monthly_match:
            stats['monthly_est'] = f"${monthly_match.group(1)}"
        
        # Parse today's stats from the daily table
        # The tracker now shows dates in PST, so use local PST time
        today = datetime.now().strftime('%m-%d')
            
        today_pattern = rf'│\s*{today}\s*│\s*([\d,]+)\s*│\s*\$\s*([\d,]+\.?\d*)'
        today_match = re.search(today_pattern, output)
        if today_match:
            stats['today_requests'] = today_match.group(1).strip()
            stats['today_cost'] = f"${today_match.group(2).strip()}"
        
        return stats
    
    @rumps.clicked("Refresh Now")
    def refresh_clicked(self, _):
        """Manual refresh button"""
        self.refresh_stats()
    
    @rumps.clicked("Auto-refresh: ON", "Auto-refresh: OFF")
    def toggle_auto_refresh(self, sender):
        """Toggle auto-refresh on/off"""
        self.auto_refresh = not self.auto_refresh
        sender.title = f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'}"
    
    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()
    
    @rumps.clicked("Sync to iCloud")
    def sync_to_icloud(self, _):
        """Sync local usage data to iCloud"""
        rumps.notification("Claude Usage Tracker", "Syncing to iCloud", "Starting sync...")
        
        try:
            result = subprocess.run(
                ['python3', self.script_path, '--sync'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse sync results
                output = result.stdout.strip()
                if "Successfully synced" in output:
                    rumps.notification("Claude Usage Tracker", "Sync Complete", "Data synced to iCloud successfully")
                elif output:
                    rumps.notification("Claude Usage Tracker", "Sync Complete", output)
                else:
                    rumps.notification("Claude Usage Tracker", "Sync Complete", "Data synced to iCloud")
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                rumps.notification("Claude Usage Tracker", "Sync Failed", error_msg)
        
        except subprocess.TimeoutExpired:
            rumps.notification("Claude Usage Tracker", "Sync Failed", "Operation timed out")
        except Exception as e:
            rumps.notification("Claude Usage Tracker", "Sync Failed", str(e))
    
    @rumps.clicked("Reconcile All Macs")
    def reconcile_all_macs(self, _):
        """Reconcile data from all synced machines"""
        rumps.notification("Claude Usage Tracker", "Reconciling Data", "Combining data from all Macs...")
        
        try:
            result = subprocess.run(
                ['python3', self.script_path, '--reconcile'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse reconcile results
                output = result.stdout.strip()
                # Look for reconciliation stats in output
                if "Reconciled" in output and "unique sessions" in output:
                    # Extract the number of sessions reconciled
                    sessions_match = re.search(r'Reconciled (\d+) unique sessions', output)
                    if sessions_match:
                        sessions = sessions_match.group(1)
                        rumps.notification("Claude Usage Tracker", "Reconcile Complete", f"Reconciled {sessions} sessions from all Macs")
                    else:
                        rumps.notification("Claude Usage Tracker", "Reconcile Complete", "Data reconciled successfully")
                elif output:
                    rumps.notification("Claude Usage Tracker", "Reconcile Complete", output)
                else:
                    rumps.notification("Claude Usage Tracker", "Reconcile Complete", "Data reconciled successfully")
            else:
                # Check if error is due to missing sync directory
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip() if result.stdout else "Unknown error"
                if "does not exist" in error_msg or "No such file or directory" in error_msg:
                    rumps.notification("Claude Usage Tracker", "Reconcile Failed", "No synced data found. Run 'Sync to iCloud' first.")
                else:
                    rumps.notification("Claude Usage Tracker", "Reconcile Failed", error_msg)
        
        except subprocess.TimeoutExpired:
            rumps.notification("Claude Usage Tracker", "Reconcile Failed", "Operation timed out")
        except Exception as e:
            rumps.notification("Claude Usage Tracker", "Reconcile Failed", str(e))
    
    @rumps.clicked("View Combined Stats")
    def view_combined_stats(self, _):
        """View combined statistics from all Macs"""
        try:
            result = subprocess.run(
                ['python3', self.script_path, '--from-reconciled'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse and show key stats in a window
                stats = self.parse_usage_output(result.stdout)
                
                # Create a formatted message
                message = f"""Combined Stats from All Macs:

Total Requests: {stats['total_requests']}
Total Cost: {stats['total_cost']}
Daily Average: {stats['daily_avg']}
Monthly Estimate: {stats['monthly_est']}

Today's Requests: {stats['today_requests']}
Today's Cost: {stats['today_cost']}"""
                
                rumps.alert("Combined Claude Usage Stats", message)
            else:
                rumps.alert("Error", f"Failed to get combined stats: {result.stderr or 'Unknown error'}")
        
        except subprocess.TimeoutExpired:
            rumps.alert("Error", "Operation timed out")
        except Exception as e:
            rumps.alert("Error", f"Failed to get combined stats: {str(e)}")
    
    @rumps.clicked("Sync Status")
    def show_sync_status(self, _):
        """Show sync status information"""
        try:
            result = subprocess.run(
                ['python3', self.script_path, '--sync-status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Show sync status in an alert
                rumps.alert("Sync Status", result.stdout.strip())
            else:
                rumps.alert("Error", f"Failed to get sync status: {result.stderr or 'Unknown error'}")
        
        except subprocess.TimeoutExpired:
            rumps.alert("Error", "Operation timed out")
        except Exception as e:
            rumps.alert("Error", f"Failed to get sync status: {str(e)}")
    
    def refresh_stats(self):
        """Refresh usage statistics from the tracker script"""
        try:
            # Run the usage tracker script
            result = subprocess.run(
                ['python3', self.script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                stats = self.parse_usage_output(result.stdout)
                
                # Update menu bar title with TODAY's requests and cost
                if stats['today_requests'] != 'N/A':
                    self.title = f"Claude: {stats['today_requests']} reqs | {stats['today_cost']}"
                else:
                    # When no data for today, show 0 instead of total
                    self.title = f"Claude: 0 reqs | $0.00"
                
                # Update menu items
                self.menu["Today's Requests: Loading..."].title = f"Today's Requests: {stats['today_requests']}"
                self.menu["Today's Cost: Loading..."].title = f"Today's Cost: {stats['today_cost']}"
                self.menu["30-Day Average: Loading..."].title = f"30-Day Average: {stats['daily_avg']}"
                self.menu["Monthly Total: Loading..."].title = f"Monthly Total: {stats['total_cost']}"
            else:
                self.title = "Claude: Error"
                print(f"Error running tracker: {result.stderr}")
        
        except Exception as e:
            self.title = "Claude: Error"
            print(f"Exception: {e}")

if __name__ == "__main__":
    # Check if rumps is installed
    try:
        import rumps
    except ImportError:
        print("Installing required package: rumps")
        subprocess.run(['pip3', 'install', 'rumps'], check=True)
        import rumps
    
    app = ClaudeUsageMenuBarApp()
    app.run()