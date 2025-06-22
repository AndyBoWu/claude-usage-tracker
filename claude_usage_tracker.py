#!/usr/bin/env python3
"""
Claude Code Usage Tracker - Public Version

IMPORTANT: Run this script periodically (daily recommended) as Claude Code may purge 
local conversation logs after an unknown retention period (estimated 30 days based on 
feedback transcript retention policy). Set up a cron job to preserve your usage history.

Example crontab entry (runs daily at 8 AM):
0 8 * * * cd /path/to/script && python3 PUBLIC_claude_usage_tracker.py >/dev/null 2>&1

This script analyzes Claude Code conversation logs to provide token usage statistics,
cost tracking, and model usage breakdown across sessions and time periods.

SETUP INSTRUCTIONS:
1. Modify the shebang line (line 1) if your Python installation is elsewhere
2. Verify that your Claude Code logs are in the default location: ~/.claude/projects/
3. If Claude Code is installed elsewhere, use --claude-dir argument to specify location
4. No other customization should be needed for most users

Data source: ~/.claude/projects/*/conversation_uuid.jsonl files
"""

import json
import os
import glob
from datetime import datetime, timezone, timedelta
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple, Optional
import argparse
import csv
import urllib.parse
from zoneinfo import ZoneInfo

# Usage data structure
Usage = namedtuple('Usage', ['input_tokens', 'output_tokens', 'cache_creation_tokens', 'cache_read_tokens', 'cost_usd', 'model', 'timestamp', 'project_name', 'session_id'])

class ClaudeUsageTracker:
    def __init__(self, claude_dir: str = None):
        # CUSTOMIZATION: If Claude Code stores data elsewhere, modify the default path below
        # Default: ~/.claude (standard Claude Code installation)
        # Custom example: "/custom/path/to/.claude"
        self.claude_dir = claude_dir or os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.claude_dir, "projects")
        
        # Current Claude API pricing (per million tokens) as of 2025
        # CUSTOMIZATION: Update these prices if they change in the future
        # Note: The actual costs are taken from Claude Code logs which reflect 
        # real API charges including cache pricing adjustments
        self.model_pricing = {
            'claude-sonnet-4-20250514': {
                'input': 3.00,
                'output': 15.00,
                'cache_creation': 3.75,  # 25% premium
                'cache_read': 0.30,      # 90% discount
                'name': 'Claude Sonnet 4'
            },
            'claude-opus-4': {
                'input': 15.00,
                'output': 75.00, 
                'cache_creation': 18.75,
                'cache_read': 1.50,
                'name': 'Claude Opus 4'
            },
            'claude-opus-4-20250514': {
                'input': 15.00,
                'output': 75.00, 
                'cache_creation': 18.75,
                'cache_read': 1.50,
                'name': 'Claude Opus 4'
            },
            'claude-3-5-sonnet-20241022': {
                'input': 3.00,
                'output': 15.00,
                'cache_creation': 3.75,
                'cache_read': 0.30,
                'name': 'Claude 3.5 Sonnet'
            },
            'claude-3-5-haiku-20241022': {
                'input': 0.80,
                'output': 4.00,
                'cache_creation': 1.00,
                'cache_read': 0.08,
                'name': 'Claude 3.5 Haiku'
            }
            # CUSTOMIZATION: Add new models here as they become available
            # Format: 'model-id': {'input': price, 'output': price, 'cache_creation': price, 'cache_read': price, 'name': 'Display Name'}
        }
    
    def get_model_info(self, model_id: str) -> dict:
        """Get pricing and display info for a model."""
        return self.model_pricing.get(model_id, {
            'input': 0.00,
            'output': 0.00,
            'cache_creation': 0.00,
            'cache_read': 0.00,
            'name': model_id
        })
        
    def get_all_conversation_files(self) -> List[str]:
        """Find all JSONL conversation files in Claude projects."""
        # CUSTOMIZATION: If Claude Code uses a different file pattern, modify this
        # Current pattern: ~/.claude/projects/*/conversation_uuid.jsonl
        pattern = os.path.join(self.projects_dir, "*", "*.jsonl")
        return glob.glob(pattern)
    
    def extract_project_name(self, file_path: str) -> str:
        """Extract project name from file path."""
        try:
            # Extract the project directory name
            project_dir = os.path.basename(os.path.dirname(file_path))
            
            # URL decode the project name (Claude Code encodes project paths)
            if project_dir.startswith('-'):
                project_dir = project_dir[1:]  # Remove leading dash
            
            # Replace dashes with slashes to reconstruct path
            decoded_name = project_dir.replace('-', '/')
            
            # Extract just the final directory name for readability
            if '/' in decoded_name:
                return decoded_name.split('/')[-1]
            
            return decoded_name
        except:
            return "unknown"
    
    def parse_conversation_file(self, file_path: str) -> List[Usage]:
        """Parse a single JSONL conversation file and extract usage data."""
        usage_records = []
        project_name = self.extract_project_name(file_path)
        session_id = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Only process assistant messages with usage data
                        # CUSTOMIZATION: If Claude Code log format changes, modify these field names
                        if (data.get('type') == 'assistant' and 
                            'message' in data and 
                            'usage' in data['message']):
                            
                            usage = data['message']['usage']
                            model = data['message'].get('model', 'unknown')
                            timestamp = data.get('timestamp', '')
                            
                            # Calculate cost since it's not in the logs
                            model_info = self.get_model_info(model)
                            cost = (
                                (usage.get('input_tokens', 0) * model_info['input'] / 1_000_000) +
                                (usage.get('output_tokens', 0) * model_info['output'] / 1_000_000) +
                                (usage.get('cache_creation_input_tokens', 0) * model_info['cache_creation'] / 1_000_000) +
                                (usage.get('cache_read_input_tokens', 0) * model_info['cache_read'] / 1_000_000)
                            )
                            
                            # Parse timestamp
                            dt = None
                            if timestamp:
                                try:
                                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                except ValueError:
                                    dt = None
                            
                            # CUSTOMIZATION: If Claude Code changes usage field names, update these
                            usage_record = Usage(
                                input_tokens=usage.get('input_tokens', 0),
                                output_tokens=usage.get('output_tokens', 0),
                                cache_creation_tokens=usage.get('cache_creation_input_tokens', 0),
                                cache_read_tokens=usage.get('cache_read_input_tokens', 0),
                                cost_usd=cost,
                                model=model,
                                timestamp=dt,
                                project_name=project_name,
                                session_id=session_id
                            )
                            
                            usage_records.append(usage_record)
                            
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON in {file_path}:{line_num}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return usage_records
    
    def collect_all_usage(self) -> List[Usage]:
        """Collect usage data from all conversation files."""
        all_usage = []
        files = self.get_all_conversation_files()
        
        for file_path in files:
            usage_records = self.parse_conversation_file(file_path)
            all_usage.extend(usage_records)
            
        return all_usage
    
    def analyze_usage_periods(self, usage_data: List[Usage]) -> Dict:
        """Analyze usage data for multiple time periods (7, 30, 60 days)."""
        now = datetime.now(timezone.utc)
        
        # CUSTOMIZATION: Modify these periods if you want different time ranges
        periods = {
            '7_days': now - timedelta(days=7),
            '30_days': now - timedelta(days=30),
            '60_days': now - timedelta(days=60)
        }
        
        period_analyses = {}
        
        # Analyze all time
        period_analyses['all_time'] = self.analyze_usage(usage_data)
        
        # Analyze specific periods
        for period_name, start_date in periods.items():
            period_data = [u for u in usage_data if u.timestamp and u.timestamp >= start_date]
            if period_data:
                period_analyses[period_name] = self.analyze_usage(period_data, start_date)
            else:
                period_analyses[period_name] = None
                
        return period_analyses
    
    def analyze_usage(self, usage_data: List[Usage], 
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> Dict:
        """Analyze usage data and return statistics."""
        
        # Filter by date range if provided
        filtered_data = usage_data
        if start_date or end_date:
            filtered_data = []
            for usage in usage_data:
                if usage.timestamp is None:
                    continue
                if start_date and usage.timestamp < start_date:
                    continue
                if end_date and usage.timestamp > end_date:
                    continue
                filtered_data.append(usage)
        
        # Calculate totals
        total_input_tokens = sum(u.input_tokens for u in filtered_data)
        total_output_tokens = sum(u.output_tokens for u in filtered_data)
        total_cache_creation_tokens = sum(u.cache_creation_tokens for u in filtered_data)
        total_cache_read_tokens = sum(u.cache_read_tokens for u in filtered_data)
        total_cost = sum(u.cost_usd for u in filtered_data)
        
        # Model breakdown
        model_stats = defaultdict(lambda: {
            'input_tokens': 0, 'output_tokens': 0, 
            'cache_creation_tokens': 0, 'cache_read_tokens': 0,
            'cost_usd': 0.0, 'requests': 0
        })
        
        for usage in filtered_data:
            model = usage.model
            model_stats[model]['input_tokens'] += usage.input_tokens
            model_stats[model]['output_tokens'] += usage.output_tokens
            model_stats[model]['cache_creation_tokens'] += usage.cache_creation_tokens
            model_stats[model]['cache_read_tokens'] += usage.cache_read_tokens
            model_stats[model]['cost_usd'] += usage.cost_usd
            model_stats[model]['requests'] += 1
        
        # Daily breakdown
        daily_stats = defaultdict(lambda: {
            'input_tokens': 0, 'output_tokens': 0,
            'cache_creation_tokens': 0, 'cache_read_tokens': 0,
            'cost_usd': 0.0, 'requests': 0
        })
        
        for usage in filtered_data:
            if usage.timestamp:
                # Convert UTC timestamp to PST for display
                pst_timestamp = usage.timestamp.astimezone(ZoneInfo('America/Los_Angeles'))
                date_key = pst_timestamp.date().isoformat()
                daily_stats[date_key]['input_tokens'] += usage.input_tokens
                daily_stats[date_key]['output_tokens'] += usage.output_tokens
                daily_stats[date_key]['cache_creation_tokens'] += usage.cache_creation_tokens
                daily_stats[date_key]['cache_read_tokens'] += usage.cache_read_tokens
                daily_stats[date_key]['cost_usd'] += usage.cost_usd
                daily_stats[date_key]['requests'] += 1
        
        # Calculate averages
        total_days = len(daily_stats) if daily_stats else 1
        
        # Last 30 days for more accurate daily average
        recent_days = sorted(daily_stats.items(), key=lambda x: x[0], reverse=True)[:30]
        recent_total_tokens = sum(stats['input_tokens'] + stats['output_tokens'] + 
                                stats['cache_creation_tokens'] for _, stats in recent_days)
        recent_total_cost = sum(stats['cost_usd'] for _, stats in recent_days)
        recent_days_count = len(recent_days) if recent_days else 1
        
        daily_avg_tokens = recent_total_tokens / recent_days_count
        daily_avg_cost = recent_total_cost / recent_days_count
        monthly_est_tokens = daily_avg_tokens * 30
        monthly_est_cost = daily_avg_cost * 30
        
        # Calculate API pay-as-you-go costs
        api_cost_total = 0.0
        api_cost_by_model = {}
        
        for model, stats in model_stats.items():
            model_info = self.get_model_info(model)
            api_cost = (
                (stats['input_tokens'] * model_info['input'] / 1_000_000) +
                (stats['output_tokens'] * model_info['output'] / 1_000_000) +
                (stats['cache_creation_tokens'] * model_info['cache_creation'] / 1_000_000) +
                (stats['cache_read_tokens'] * model_info['cache_read'] / 1_000_000)
            )
            api_cost_by_model[model] = api_cost
            api_cost_total += api_cost
        
        # Calculate daily API cost average
        daily_avg_api_cost = api_cost_total / total_days if total_days > 0 else 0
        monthly_est_api_cost = daily_avg_api_cost * 30
        
        return {
            'summary': {
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_cache_creation_tokens': total_cache_creation_tokens,
                'total_cache_read_tokens': total_cache_read_tokens,
                'total_tokens': total_input_tokens + total_output_tokens + total_cache_creation_tokens,
                'total_cost_usd': total_cost,
                'total_api_cost_usd': api_cost_total,
                'total_requests': len(filtered_data),
                'daily_avg_tokens': daily_avg_tokens,
                'daily_avg_cost': daily_avg_cost,
                'daily_avg_api_cost': daily_avg_api_cost,
                'monthly_est_tokens': monthly_est_tokens,
                'monthly_est_cost': monthly_est_cost,
                'monthly_est_api_cost': monthly_est_api_cost,
                'total_days': total_days,
                'recent_days_count': recent_days_count,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'by_model': dict(model_stats),
            'by_day': dict(daily_stats),
            'api_cost_by_model': api_cost_by_model
        }
    
    def print_multi_period_report(self, period_analyses: Dict, usage_data: List[Usage] = None):
        """Print a formatted usage report with multiple time periods."""
        print("\n💰 CLAUDE CODE USAGE SUMMARY")
        print("─" * 50)
        
        # Use 30-day data if available, otherwise fall back to all-time
        target_period = period_analyses.get('30_days') or period_analyses['all_time']
        summary = target_period['summary']
        
        # Key metrics
        period_label = "30 days" if period_analyses.get('30_days') else f"{summary['total_days']} days"
        print(f"\n📊 USAGE ({period_label}):")
        print(f"  Total requests: {summary['total_requests']:,}")
        print(f"  Total tokens: {summary['total_tokens']:,}")
        
        # Cost summary
        max_plan_cost = 200.00
        actual_cost = min(summary['total_api_cost_usd'], max_plan_cost)
        savings = summary['total_api_cost_usd'] - actual_cost
        
        print(f"\n💵 COSTS:")
        print(f"  API equivalent: ${summary['total_api_cost_usd']:.2f}")
        print(f"  Your cost: ${actual_cost:.2f} (Max plan)")
        print(f"  You saved: ${savings:.2f}")
        
        # Daily and monthly projections
        print(f"\n📈 PROJECTIONS:")
        print(f"  Daily average: ${summary['daily_avg_api_cost']:.2f}")
        print(f"  Monthly estimate: ${summary['monthly_est_api_cost']:.2f}")
        
        # Model breakdown (simplified)
        print(f"\n🤖 MODEL USAGE:")
        for model, stats in target_period['by_model'].items():
            if stats['requests'] == 0:  # Skip unused models
                continue
            model_info = self.get_model_info(model)
            api_cost = target_period.get('api_cost_by_model', {}).get(model, 0.0)
            print(f"  {model_info['name']}: {stats['requests']:,} requests → ${api_cost:.2f}")
        
        # Recent activity (last 30 days)
        activity_period = period_analyses.get('30_days') or period_analyses['all_time']
        if activity_period:
            daily_items = sorted(activity_period['by_day'].items(), key=lambda x: x[0], reverse=True)
            
            # Print cost breakdown chart only
            self.print_cost_line_chart(daily_items)
    
    def get_color_for_requests(self, requests: int, max_requests: int) -> str:
        """Return ANSI color code based on request volume ranges."""
        # Calculate percentage of max requests
        percentage = (requests / max_requests) * 100 if max_requests > 0 else 0
        
        # Color scheme based on productivity/effort level
        if percentage >= 80:  # Very high productivity (80-100%)
            return '\033[95m'  # Bright magenta (noble/royal excellence!)
        elif percentage >= 60:  # High productivity (60-79%)
            return '\033[96m'  # Bright cyan (great effort)
        elif percentage >= 40:  # Medium productivity (40-59%)
            return '\033[94m'  # Bright blue (good work)
        elif percentage >= 20:  # Low productivity (20-39%)
            return '\033[93m'  # Bright yellow (moderate effort)
        else:  # Very low productivity (0-19%)
            return '\033[91m'  # Bright red (low activity)
    
    def print_activity_chart(self, daily_items: List[Tuple[str, Dict]], max_width: int = 50):
        """Print ASCII time series chart with dual y-axis for requests and costs."""
        if not daily_items:
            return
            
        # Get data in chronological order (oldest first)
        chart_data = [(date, stats['requests'], stats['cost_usd']) for date, stats in reversed(daily_items)]
        
        if not chart_data:
            return
            
        # Find max values for scaling
        max_requests = max(requests for _, requests, _ in chart_data)
        max_cost = max(cost for _, _, cost in chart_data)
        
        if max_requests == 0 and max_cost == 0:
            return
        
        # Calculate chart dimensions
        chart_height = 15  # Height of the chart area
        
        print(f"\n  📊 Activity Time Series (Last {len(chart_data)} days)")
        print(f"  Requests: Max {max_requests:,} | Cost: Max ${max_cost:.2f}")
        print()
        
        # Print the time series chart
        # Y-axis labels
        for i in range(chart_height, -1, -1):
            # Calculate values for this height
            request_value = int((i / chart_height) * max_requests) if chart_height > 0 else 0
            cost_value = (i / chart_height) * max_cost if chart_height > 0 else 0
            
            # Format y-axis labels
            if i == chart_height:
                req_label = f"{request_value:>5}"
                cost_label = f"${cost_value:>6.2f}"
            elif i == 0:
                req_label = "    0"
                cost_label = "  $0.00"
            elif i % 3 == 0:  # Show labels every 3 lines
                req_label = f"{request_value:>5}"
                cost_label = f"${cost_value:>6.2f}"
            else:
                req_label = "     "
                cost_label = "       "
            
            # Print the row
            print(f"  {req_label} │", end="")
            
            # Plot data points
            for date, requests, cost in chart_data:
                # Calculate if this point should be plotted at this height
                req_height = int((requests / max_requests) * chart_height) if max_requests > 0 else 0
                cost_height = int((cost / max_cost) * chart_height) if max_cost > 0 else 0
                
                if req_height == i:
                    # Color based on request volume
                    color_code = self.get_color_for_requests(requests, max_requests)
                    print(f"{color_code}●\033[0m", end="")
                elif cost_height == i:
                    print("○", end="")  # Cost marker
                elif i == 0:
                    print("─", end="")  # X-axis line
                else:
                    print(" ", end="")
            
            print(f"│ {cost_label}")
        
        # X-axis labels
        print(f"  {'Reqs':>5} └", end="")
        print("─" * len(chart_data), end="")
        print("┘ Cost")
        
        # Date labels (show every nth date to avoid crowding)
        print("        ", end="")
        date_interval = max(1, len(chart_data) // 10)  # Show ~10 date labels
        for i, (date, _, _) in enumerate(chart_data):
            if i % date_interval == 0 or i == len(chart_data) - 1:
                # Extract month-day
                short_date = date[-5:] if len(date) >= 5 else date
                # Pad or truncate to fit
                print(f"{short_date:<{date_interval}}", end="")
            else:
                print(" ", end="")
        print()
        
        # Legend
        print("\n  Legend: ", end="")
        print("\033[91m●\033[0m Low ", end="")
        print("\033[93m●\033[0m Moderate ", end="")
        print("\033[94m●\033[0m Good ", end="")
        print("\033[96m●\033[0m High ", end="")
        print("\033[95m●\033[0m Peak activity ", end="")
        print("○ Cost")
        
        # Summary stats
        total_requests = sum(r for _, r, _ in chart_data)
        total_cost = sum(c for _, _, c in chart_data)
        avg_requests = total_requests / len(chart_data) if chart_data else 0
        avg_cost = total_cost / len(chart_data) if chart_data else 0
        
        print(f"\n  Period totals: {total_requests:,} requests, ${total_cost:.2f}")
        print(f"  Daily average: {avg_requests:.0f} requests, ${avg_cost:.2f}")
    
    def print_cost_line_chart(self, daily_items: List[Tuple[str, Dict]]):
        """Print a bar chart for daily cost breakdown."""
        if not daily_items:
            return
            
        # Get data in chronological order for the last 15 days
        chart_data = [(date, stats['cost_usd'], stats['requests']) for date, stats in reversed(daily_items[:15])]
        
        if not chart_data:
            return
            
        # Find max cost for scaling
        max_cost = max(cost for _, cost, _ in chart_data)
        if max_cost == 0:
            return
            
        chart_height = 10  # Height of the chart
        
        print(f"\n💰 Daily Cost Breakdown (Last {len(chart_data)} Days)")
        print("─" * 80)
        
        # Print the bar chart
        for row in range(chart_height, -1, -1):
            # Y-axis label
            if row == chart_height:
                cost_value = max_cost
                label = f"${cost_value:>7.2f}"
            elif row == 0:
                label = "   $0.00"
            elif row % 2 == 0:
                cost_value = max_cost * row / chart_height
                label = f"${cost_value:>7.2f}"
            else:
                label = "        "
            
            # Print row
            print(f"{label} │", end="")
            
            # Print bars
            for i, (date, cost, requests) in enumerate(chart_data):
                bar_height = int((cost / max_cost) * chart_height) if max_cost > 0 else 0
                
                # Determine bar character and color
                if row == 0:
                    # Base line
                    print("─────", end="")
                elif row <= bar_height:
                    # Color based on cost percentage
                    percentage = cost / max_cost if max_cost > 0 else 0
                    if percentage >= 0.8:
                        # Red for high costs (80%+)
                        print("\033[91m█████\033[0m", end="")
                    elif percentage >= 0.6:
                        # Yellow for medium-high costs (60-80%)
                        print("\033[93m█████\033[0m", end="")
                    elif percentage >= 0.4:
                        # Blue for medium costs (40-60%)
                        print("\033[94m█████\033[0m", end="")
                    elif percentage >= 0.2:
                        # Cyan for low-medium costs (20-40%)
                        print("\033[96m█████\033[0m", end="")
                    else:
                        # Green for low costs (0-20%)
                        print("\033[92m█████\033[0m", end="")
                else:
                    print("     ", end="")
                
                # Add spacing between bars
                if i < len(chart_data) - 1:
                    print(" ", end="")
            
            print("│")
        
        # X-axis base line
        print("         └", end="")
        print("─" * (len(chart_data) * 6 - 1) + "┘")
        
        # X-axis date labels
        print("          ", end="")
        for i, (date, _, _) in enumerate(chart_data):
            date_str = date[5:10]  # MM-DD format
            print(f"{date_str}", end="")
            if i < len(chart_data) - 1:
                print(" ", end="")
        print()
        
        # Legend
        print("\n📊 Legend: ", end="")
        print("\033[91m█\033[0m 80%+ ", end="")
        print("\033[93m█\033[0m 60-80% ", end="")
        print("\033[94m█\033[0m 40-60% ", end="")
        print("\033[96m█\033[0m 20-40% ", end="")
        print("\033[92m█\033[0m 0-20%")
        
        # Summary statistics
        total_cost = sum(cost for _, cost, _ in chart_data)
        total_requests = sum(requests for _, _, requests in chart_data)
        avg_cost = total_cost / len(chart_data) if chart_data else 0
        avg_requests = total_requests / len(chart_data) if chart_data else 0
        min_cost = min(cost for _, cost, _ in chart_data) if chart_data else 0
        max_requests = max(requests for _, _, requests in chart_data) if chart_data else 0
        
        print(f"\n📈 Summary:")
        print(f"   Total: ${total_cost:,.2f} | Daily avg: ${avg_cost:.2f}")
        print(f"   Peak: ${max_cost:.2f} | Low: ${min_cost:.2f}")
        
        # Add daily requests table
        print(f"\n📊 Daily Requests (Last {len(chart_data)} Days)")
        print("─" * 80)
        print("│ Date       │ Requests │ Cost       │ Avg Token/Req │")
        print("├────────────┼──────────┼────────────┼───────────────┤")
        
        for date, cost, requests in chart_data:
            date_str = date[5:10]  # MM-DD format
            # Calculate average tokens per request (rough estimate based on cost)
            avg_tokens = int((cost / requests * 1000) / 0.003) if requests > 0 else 0
            print(f"│ {date_str}      │ {requests:>8,} │ ${cost:>9.2f} │ {avg_tokens:>13,} │")
        
        print("├────────────┼──────────┼────────────┼───────────────┤")
        print(f"│ Total      │ {total_requests:>8,} │ ${total_cost:>9.2f} │ {int(total_cost/total_requests*1000/0.003) if total_requests > 0 else 0:>13,} │")
        print("└────────────┴──────────┴────────────┴───────────────┘")

    def print_report(self, analysis: Dict, show_detail: bool = False):
        """Print a formatted usage report (legacy method for date-filtered reports)."""
        summary = analysis['summary']
        
        print("=" * 60)
        print("CLAUDE CODE USAGE REPORT")
        print("=" * 60)
        
        # Summary
        print(f"\nSUMMARY:")
        print(f"  Total Requests: {summary['total_requests']:,}")
        print(f"  Total Input Tokens: {summary['total_input_tokens']:,}")
        print(f"  Total Output Tokens: {summary['total_output_tokens']:,}")
        print(f"  Total Cache Creation Tokens: {summary['total_cache_creation_tokens']:,}")
        print(f"  Total Cache Read Tokens: {summary['total_cache_read_tokens']:,}")
        print(f"  Total Tokens: {summary['total_tokens']:,}")
        print(f"  Total Cost: ${summary['total_cost_usd']:.4f}")
        
        if summary['date_range']['start'] or summary['date_range']['end']:
            print(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        
        # Averages
        print(f"\nAVERAGES:")
        print(f"  Daily Average (Last {summary['recent_days_count']} days): {summary['daily_avg_tokens']:,.0f} tokens, ${summary['daily_avg_cost']:.2f}")
        print(f"  Monthly Estimate: {summary['monthly_est_tokens']:,.0f} tokens, ${summary['monthly_est_cost']:.2f}")
        
        # Model breakdown
        print(f"\nBY MODEL:")
        for model, stats in analysis['by_model'].items():
            model_info = self.get_model_info(model)
            print(f"  {model_info['name']} ({model}):")
            print(f"    Requests: {stats['requests']:,}")
            print(f"    Input Tokens: {stats['input_tokens']:,} (${model_info['input']}/M)")
            print(f"    Output Tokens: {stats['output_tokens']:,} (${model_info['output']}/M)")
            print(f"    Cache Creation: {stats['cache_creation_tokens']:,} (${model_info['cache_creation']}/M)")
            print(f"    Cache Read: {stats['cache_read_tokens']:,} (${model_info['cache_read']}/M)")
            print(f"    Actual Cost: ${stats['cost_usd']:.4f} (from Claude Code logs)")
            
            # Calculate what cost should be based on current pricing
            calc_cost = (
                (stats['input_tokens'] * model_info['input'] / 1_000_000) +
                (stats['output_tokens'] * model_info['output'] / 1_000_000) +
                (stats['cache_creation_tokens'] * model_info['cache_creation'] / 1_000_000) +
                (stats['cache_read_tokens'] * model_info['cache_read'] / 1_000_000)
            )
            print(f"    Calculated Cost: ${calc_cost:.4f} (using current pricing)")
            
            if abs(stats['cost_usd'] - calc_cost) > 0.01:
                print(f"    Note: Difference of ${abs(stats['cost_usd'] - calc_cost):.4f} may indicate pricing changes")
        
        # Daily usage breakdown
        if show_detail:
            print(f"\nDETAILED DAILY BREAKDOWN (All Days):")
            # Show ALL days from first usage to current, chronologically
            daily_items = sorted(analysis['by_day'].items(), key=lambda x: x[0])
            
            for date, stats in daily_items:
                total_tokens = stats['input_tokens'] + stats['output_tokens'] + stats['cache_creation_tokens']
                print(f"  {date}: {total_tokens:,} tokens, ${stats['cost_usd']:.2f}, {stats['requests']} requests")
                print(f"    Input: {stats['input_tokens']:,} | Output: {stats['output_tokens']:,} | Cache Creation: {stats['cache_creation_tokens']:,} | Cache Read: {stats['cache_read_tokens']:,}")
        else:
            # Recent daily usage (last 10 days)
            print(f"\nRECENT DAILY USAGE:")
            daily_items = sorted(analysis['by_day'].items(), key=lambda x: x[0], reverse=True)[:10]
            
            for date, stats in daily_items:
                total_tokens = stats['input_tokens'] + stats['output_tokens'] + stats['cache_creation_tokens']
                print(f"  {date}: {total_tokens:,} tokens, ${stats['cost_usd']:.4f}, {stats['requests']} requests")


def main():
    parser = argparse.ArgumentParser(description='Track Claude Code token usage and costs')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD) for legacy compatibility')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD) for legacy compatibility')
    parser.add_argument('--claude-dir', type=str, help='Path to .claude directory (default: ~/.claude)')
    parser.add_argument('--json', action='store_true', help='Output as JSON instead of formatted report')
    
    args = parser.parse_args()
    
    # Initialize tracker
    tracker = ClaudeUsageTracker(args.claude_dir)
    
    # Collect and analyze usage
    usage_data = tracker.collect_all_usage()
    
    if not usage_data:
        print("No usage data found in Claude Code logs.")
        print("Make sure Claude Code is installed and you have used it to generate some conversations.")
        print("Default log location: ~/.claude/projects/")
        return 1
    
    # Handle legacy date filtering if provided
    if args.start_date or args.end_date:
        start_date = None
        end_date = None
        
        if args.start_date:
            try:
                start_date = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
            except ValueError:
                print(f"Error: Invalid start date format: {args.start_date}")
                return 1
                
        if args.end_date:
            try:
                end_date = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
            except ValueError:
                print(f"Error: Invalid end date format: {args.end_date}")
                return 1
        
        # Legacy single-period analysis
        analysis = tracker.analyze_usage(usage_data, start_date, end_date)
        
        if args.json:
            print(json.dumps(analysis, indent=2, default=str))
        else:
            tracker.print_report(analysis, show_detail=True)
            
        # Use legacy analysis for CSV export
        export_analysis = analysis
    else:
        # New multi-period analysis (default behavior)
        period_analyses = tracker.analyze_usage_periods(usage_data)
        
        if args.json:
            print(json.dumps(period_analyses, indent=2, default=str))
        else:
            tracker.print_multi_period_report(period_analyses, usage_data)
        
        # Use all-time analysis for CSV export
        export_analysis = period_analyses['all_time']
    
    
    return 0


def export_to_csv(usage_data: List[Usage], analysis: Dict, filename: str):
    """Export detailed usage data to CSV."""
    
    # Create a tracker instance to access model pricing info
    tracker = ClaudeUsageTracker()
    
    # CUSTOMIZATION: Modify the CSV output directory by changing the filename path
    # Default: saves to current working directory
    # Example: filename = f"/path/to/exports/{filename}"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write summary header
        writer.writerow(['# CLAUDE CODE USAGE EXPORT'])
        writer.writerow(['# Generated:', datetime.now().isoformat()])
        writer.writerow(['# Total Records:', len(usage_data)])
        writer.writerow(['# Total Cost (Actual from logs):', f"${analysis['summary']['total_cost_usd']:.4f}"])
        writer.writerow(['# Daily Average:', f"{analysis['summary']['daily_avg_tokens']:,.0f} tokens, ${analysis['summary']['daily_avg_cost']:.2f}"])
        writer.writerow(['# Monthly Estimate:', f"{analysis['summary']['monthly_est_tokens']:,.0f} tokens, ${analysis['summary']['monthly_est_cost']:.2f}"])
        writer.writerow([])
        
        # Write model pricing information
        writer.writerow(['# MODEL PRICING REFERENCE (per million tokens)'])
        writer.writerow(['Model_ID', 'Display_Name', 'Input_Price', 'Output_Price', 'Cache_Creation_Price', 'Cache_Read_Price'])
        
        # Get unique models from data
        models_used = set(usage.model for usage in usage_data)
        for model in sorted(models_used):
            model_info = tracker.get_model_info(model)
            writer.writerow([
                model,
                model_info['name'],
                f"${model_info['input']:.2f}",
                f"${model_info['output']:.2f}",
                f"${model_info['cache_creation']:.2f}",
                f"${model_info['cache_read']:.2f}"
            ])
        writer.writerow([])
        
        # Write daily summary
        writer.writerow(['# DAILY SUMMARY'])
        writer.writerow(['Date', 'Total_Tokens', 'Input_Tokens', 'Output_Tokens', 
                        'Cache_Creation_Tokens', 'Cache_Read_Tokens', 'Cost_USD', 
                        'Requests', 'Avg_Cost_Per_Request'])
        
        daily_items = sorted(analysis['by_day'].items(), key=lambda x: x[0])
        for date, stats in daily_items:
            total_tokens = stats['input_tokens'] + stats['output_tokens'] + stats['cache_creation_tokens']
            avg_cost_per_request = stats['cost_usd'] / stats['requests'] if stats['requests'] > 0 else 0
            
            writer.writerow([
                date,
                total_tokens,
                stats['input_tokens'],
                stats['output_tokens'], 
                stats['cache_creation_tokens'],
                stats['cache_read_tokens'],
                f"{stats['cost_usd']:.4f}",
                stats['requests'],
                f"{avg_cost_per_request:.4f}"
            ])
        
        writer.writerow([])
        
        # Write detailed transaction data
        writer.writerow(['# DETAILED TRANSACTION DATA'])
        writer.writerow(['Timestamp', 'Date', 'Project_Name', 'Session_ID', 'Model', 
                        'Input_Tokens', 'Output_Tokens', 'Cache_Creation_Tokens', 
                        'Cache_Read_Tokens', 'Total_Tokens', 'Cost_USD'])
        
        # Sort by timestamp
        sorted_usage = sorted([u for u in usage_data if u.timestamp], 
                             key=lambda x: x.timestamp)
        
        for usage in sorted_usage:
            total_tokens = usage.input_tokens + usage.output_tokens + usage.cache_creation_tokens
            
            writer.writerow([
                usage.timestamp.isoformat() if usage.timestamp else '',
                usage.timestamp.date().isoformat() if usage.timestamp else '',
                usage.project_name,
                usage.session_id,
                usage.model,
                usage.input_tokens,
                usage.output_tokens,
                usage.cache_creation_tokens,
                usage.cache_read_tokens,
                total_tokens,
                f"{usage.cost_usd:.4f}"
            ])


if __name__ == "__main__":
    exit(main())