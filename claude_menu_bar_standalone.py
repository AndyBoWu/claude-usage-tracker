#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS - Standalone Version
Shows real-time Claude usage statistics in the macOS menu bar
This version directly imports the tracker instead of using subprocess
"""

import rumps
import json
import os
import re
from datetime import datetime, timezone, timedelta
import threading
import time
from io import StringIO
import sys
from pathlib import Path
import glob
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple, Optional
from zoneinfo import ZoneInfo

# Import the tracker module directly
from claude_usage_tracker import ClaudeUsageTracker, Usage

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Loading...", quit_button=None)
        # Clear any default menu items first
        self.menu.clear()
        self.menu = [
            "Today's Requests: Loading...",
            "Today's Cost: Loading...",
            None,  # Separator
            "30-Day Average: Loading...",
            "Monthly Total: Loading...",
            None,  # Separator
            "Refresh Now",
            "Auto-refresh: ON",
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.auto_refresh = True
        self.refresh_interval = 30  # 30 seconds
        
        # Initialize the tracker
        self.tracker = ClaudeUsageTracker()
        
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
    
    def get_usage_stats(self):
        """Get usage statistics directly from the tracker"""
        try:
            # Capture the output that would normally go to stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Run the tracker's main analysis
            conversation_files = self.tracker.get_all_conversation_files()
            all_usage = []
            for file_path in conversation_files:
                usage_data = self.tracker.extract_usage_from_file(file_path)
                all_usage.extend(usage_data)
            
            # Generate the summary
            self.tracker.print_summary(all_usage)
            
            # Get the output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            return output, all_usage
            
        except Exception as e:
            sys.stdout = old_stdout
            print(f"Error getting usage stats: {e}")
            return None, []
    
    def parse_usage_output(self, output, all_usage):
        """Parse the CLI output to extract key metrics"""
        stats = {
            'total_requests': 'N/A',
            'total_cost': 'N/A',
            'daily_avg': 'N/A',
            'monthly_est': 'N/A',
            'today_requests': 'N/A',
            'today_cost': 'N/A'
        }
        
        if not output:
            return stats
        
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
        
        # Calculate today's stats directly from usage data
        pst = ZoneInfo('America/Los_Angeles')
        today_start = datetime.now(pst).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_usage = [u for u in all_usage if today_start <= u.timestamp.astimezone(pst) < today_end]
        
        if today_usage:
            today_requests = len(today_usage)
            today_cost = sum(u.cost_usd for u in today_usage)
            stats['today_requests'] = f"{today_requests:,}"
            stats['today_cost'] = f"${today_cost:.2f}"
        else:
            stats['today_requests'] = "0"
            stats['today_cost'] = "$0.00"
        
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
    
    def refresh_stats(self):
        """Refresh usage statistics from the tracker"""
        try:
            output, all_usage = self.get_usage_stats()
            
            if output:
                stats = self.parse_usage_output(output, all_usage)
                
                # Update menu bar title with TODAY's cost only
                self.title = stats['today_cost']
                
                # Update menu items
                self.menu["Today's Requests: Loading..."].title = f"Today's Requests: {stats['today_requests']}"
                self.menu["Today's Cost: Loading..."].title = f"Today's Cost: {stats['today_cost']}"
                self.menu["30-Day Average: Loading..."].title = f"30-Day Average: {stats['daily_avg']}"
                self.menu["Monthly Total: Loading..."].title = f"Monthly Total: {stats['total_cost']}"
            else:
                self.title = "Error"
                print("Error: No output from tracker")
        
        except Exception as e:
            self.title = "Error"
            print(f"Exception in refresh_stats: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Check if rumps is installed
    try:
        import rumps
    except ImportError:
        print("Installing required package: rumps")
        import subprocess
        subprocess.run(['pip3', 'install', 'rumps'], check=True)
        import rumps
    
    app = ClaudeUsageMenuBarApp()
    app.run()