#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS - Fixed Version
Shows real-time Claude usage statistics in the macOS menu bar
This version fixes timezone and import issues
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

# Define Usage namedtuple here to avoid import issues
Usage = namedtuple('Usage', ['input_tokens', 'output_tokens', 'cache_creation_tokens', 'cache_read_tokens', 'cost_usd', 'model', 'timestamp', 'project_name', 'session_id'])

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Claude: Loading...")
        
        # Clear default menu
        self.menu.clear()
        
        # Create menu items individually to avoid duplicates
        self.today_requests = rumps.MenuItem("Today's Requests: Loading...")
        self.today_cost = rumps.MenuItem("Today's Cost: Loading...")
        self.daily_avg = rumps.MenuItem("30-Day Average: Loading...")
        self.monthly_total = rumps.MenuItem("Monthly Total: Loading...")
        self.refresh_btn = rumps.MenuItem("Refresh Now", callback=self.refresh_clicked)
        self.auto_refresh_btn = rumps.MenuItem("Auto-refresh: ON", callback=self.toggle_auto_refresh)
        self.quit_btn = rumps.MenuItem("Quit", callback=lambda _: rumps.quit_application())
        
        # Build menu
        self.menu = [
            self.today_requests,
            self.today_cost,
            None,
            self.daily_avg,
            self.monthly_total,
            None,
            self.refresh_btn,
            self.auto_refresh_btn,
            None,
            self.quit_btn
        ]
        
        self.auto_refresh = True
        self.refresh_interval = 30
        
        # Initialize paths
        self.claude_dir = os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.claude_dir, "projects")
        
        # Model pricing
        self.model_pricing = {
            'claude-sonnet-4-20250514': {
                'input': 3.00, 'output': 15.00,
                'cache_creation': 3.75, 'cache_read': 0.30,
                'name': 'Claude Sonnet 4'
            },
            'claude-opus-4': {
                'input': 15.00, 'output': 75.00,
                'cache_creation': 18.75, 'cache_read': 1.50,
                'name': 'Claude Opus 4'
            },
            'claude-opus-4-20250514': {
                'input': 15.00, 'output': 75.00,
                'cache_creation': 18.75, 'cache_read': 1.50,
                'name': 'Claude Opus 4'
            },
            'claude-3-5-sonnet-20241022': {
                'input': 3.00, 'output': 15.00,
                'cache_creation': 3.75, 'cache_read': 0.30,
                'name': 'Claude 3.5 Sonnet'
            },
            'claude-3-5-haiku-20241022': {
                'input': 0.80, 'output': 4.00,
                'cache_creation': 1.00, 'cache_read': 0.08,
                'name': 'Claude 3.5 Haiku'
            }
        }
        
        # Start refresh thread
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
    
    def get_all_conversation_files(self):
        """Get all conversation JSONL files"""
        pattern = os.path.join(self.projects_dir, "*", "*.jsonl")
        return glob.glob(pattern)
    
    def extract_usage_from_file(self, file_path):
        """Extract usage data from a conversation file"""
        usage_data = []
        project_name = os.path.basename(os.path.dirname(file_path))
        session_id = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                        if event.get('type') == 'claudeResponse' and 'modelInfo' in event:
                            model_info = event['modelInfo']
                            usage_info = model_info.get('usage', {})
                            
                            # Get timestamps
                            timestamp_ms = event.get('ts', 0)
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                            
                            # Get token counts
                            input_tokens = usage_info.get('inputTokens', 0)
                            output_tokens = usage_info.get('outputTokens', 0)
                            cache_creation = usage_info.get('cacheCreationInputTokens', 0)
                            cache_read = usage_info.get('cacheReadInputTokens', 0)
                            
                            # Get cost
                            cost = model_info.get('costUsd', 0.0)
                            
                            # Get model
                            model = model_info.get('model', 'unknown')
                            
                            usage_data.append(Usage(
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                cache_creation_tokens=cache_creation,
                                cache_read_tokens=cache_read,
                                cost_usd=cost,
                                model=model,
                                timestamp=timestamp,
                                project_name=project_name,
                                session_id=session_id
                            ))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return usage_data
    
    def get_usage_stats(self):
        """Get usage statistics"""
        try:
            # Get all conversation files
            conversation_files = self.get_all_conversation_files()
            
            all_usage = []
            for file_path in conversation_files:
                usage_data = self.extract_usage_from_file(file_path)
                all_usage.extend(usage_data)
            
            return all_usage
            
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return []
    
    def calculate_stats(self, all_usage):
        """Calculate statistics from usage data"""
        stats = {
            'total_requests': '0',
            'total_cost': '$0.00',
            'daily_avg': '$0.00',
            'monthly_est': '$0.00',
            'today_requests': '0',
            'today_cost': '$0.00'
        }
        
        if not all_usage:
            return stats
        
        # Total stats
        total_requests = len(all_usage)
        total_cost = sum(u.cost_usd for u in all_usage)
        stats['total_requests'] = f"{total_requests:,}"
        stats['total_cost'] = f"${total_cost:.2f}"
        
        # Get date range
        if all_usage:
            dates = [u.timestamp.date() for u in all_usage]
            min_date = min(dates)
            max_date = max(dates)
            days = (max_date - min_date).days + 1
            
            if days > 0:
                daily_avg = total_cost / days
                monthly_est = daily_avg * 30
                stats['daily_avg'] = f"${daily_avg:.2f}"
                stats['monthly_est'] = f"${monthly_est:.2f}"
        
        # Today's stats
        # Use PST timezone offset
        pst_offset = timedelta(hours=-8)
        now = datetime.now(timezone.utc) + pst_offset
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - pst_offset
        today_end = today_start + timedelta(days=1)
        
        today_usage = [u for u in all_usage if today_start <= u.timestamp < today_end]
        
        if today_usage:
            today_requests = len(today_usage)
            today_cost = sum(u.cost_usd for u in today_usage)
            stats['today_requests'] = f"{today_requests:,}"
            stats['today_cost'] = f"${today_cost:.2f}"
        
        return stats
    
    def refresh_clicked(self, _):
        """Manual refresh button"""
        self.refresh_stats()
    
    def toggle_auto_refresh(self, sender):
        """Toggle auto-refresh on/off"""
        self.auto_refresh = not self.auto_refresh
        sender.title = f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'}"
    
    def refresh_stats(self):
        """Refresh usage statistics"""
        try:
            all_usage = self.get_usage_stats()
            stats = self.calculate_stats(all_usage)
            
            # Update menu bar title
            self.title = f"Claude: {stats['today_requests']} reqs | {stats['today_cost']}"
            
            # Update menu items
            self.today_requests.title = f"Today's Requests: {stats['today_requests']}"
            self.today_cost.title = f"Today's Cost: {stats['today_cost']}"
            self.daily_avg.title = f"30-Day Average: {stats['daily_avg']}"
            self.monthly_total.title = f"Monthly Total: {stats['total_cost']}"
            
        except Exception as e:
            self.title = "Claude: Error"
            print(f"Exception in refresh_stats: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = ClaudeUsageMenuBarApp()
    app.run()