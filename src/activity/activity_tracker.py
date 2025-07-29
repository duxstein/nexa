#!/usr/bin/env python3
"""
Activity Tracker for NEXA
Tracks user activity, app usage, and provides productivity insights
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
import win32gui
import win32process
import psutil
import json
from pathlib import Path
from collections import defaultdict, deque
import sqlite3

class ActivityTracker:
    """Tracks user activity and app usage for productivity insights"""
    
    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.tracking = False
        self.track_thread = None
        
        # Database setup
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / '.nexa' / 'activity.db'
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Current session data
        self.current_session = {
            'start_time': None,
            'current_app': None,
            'app_start_time': None,
            'idle_start_time': None,
            'is_idle': False
        }
        
        # Activity categories
        self.app_categories = {
            'productivity': [
                'notepad', 'wordpad', 'winword', 'excel', 'powerpnt', 'onenote',
                'code', 'devenv', 'sublime_text', 'notepad++', 'atom', 'brackets',
                'slack', 'teams', 'zoom', 'skype', 'discord'
            ],
            'development': [
                'code', 'devenv', 'sublime_text', 'notepad++', 'atom', 'brackets',
                'pycharm', 'intellij', 'eclipse', 'netbeans', 'android-studio',
                'git', 'cmd', 'powershell', 'terminal'
            ],
            'web_browsing': [
                'chrome', 'firefox', 'edge', 'safari', 'opera', 'brave'
            ],
            'communication': [
                'slack', 'teams', 'zoom', 'skype', 'discord', 'telegram',
                'whatsapp', 'outlook', 'thunderbird'
            ],
            'entertainment': [
                'spotify', 'vlc', 'netflix', 'youtube', 'steam', 'epic',
                'origin', 'uplay', 'gog', 'twitch'
            ],
            'system': [
                'explorer', 'taskmgr', 'regedit', 'services', 'control',
                'settings', 'winver'
            ]
        }
        
        # Initialize database
        self._init_database()
        
        # Idle detection settings
        self.idle_threshold = 300  # 5 minutes in seconds
        self.last_input_time = time.time()
        
        self.logger.info("Activity tracker initialized")
    
    def _init_database(self):
        """Initialize SQLite database for activity tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        app_name TEXT NOT NULL,
                        window_title TEXT,
                        category TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_seconds INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT UNIQUE NOT NULL,
                        total_active_time INTEGER,
                        total_idle_time INTEGER,
                        most_used_app TEXT,
                        most_used_category TEXT,
                        productivity_score REAL,
                        apps_used INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS idle_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_seconds INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(app_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(date)')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    def start_tracking(self):
        """Start activity tracking"""
        if not self.tracking:
            self.tracking = True
            self.current_session['start_time'] = datetime.now()
            self.track_thread = threading.Thread(target=self._track_activity, daemon=True)
            self.track_thread.start()
            self.logger.info("Activity tracking started")
    
    def stop_tracking(self):
        """Stop activity tracking"""
        if self.tracking:
            self.tracking = False
            
            # Save current app session if any
            if self.current_session['current_app']:
                self._save_app_session()
            
            # Generate daily summary
            self._generate_daily_summary()
            
            if self.track_thread:
                self.track_thread.join(timeout=2)
            
            self.logger.info("Activity tracking stopped")
    
    def _track_activity(self):
        """Main tracking loop"""
        while self.tracking:
            try:
                current_time = datetime.now()
                
                # Get current active window
                active_app = self._get_active_application()
                
                # Check for idle state
                self._check_idle_state(current_time)
                
                # Handle app changes
                if active_app != self.current_session['current_app']:
                    self._handle_app_change(active_app, current_time)
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error in activity tracking: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _get_active_application(self) -> Optional[Dict[str, str]]:
        """Get currently active application"""
        try:
            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return None
            
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process info
            try:
                process = psutil.Process(pid)
                app_name = process.name().lower().replace('.exe', '')
                
                return {
                    'app_name': app_name,
                    'window_title': window_title,
                    'pid': pid,
                    'category': self._categorize_app(app_name)
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting active application: {e}")
            return None
    
    def _categorize_app(self, app_name: str) -> str:
        """Categorize application by name"""
        app_name = app_name.lower()
        
        for category, apps in self.app_categories.items():
            if any(app in app_name for app in apps):
                return category
        
        return 'other'
    
    def _check_idle_state(self, current_time: datetime):
        """Check if user is idle"""
        try:
            # This is a simplified idle detection
            # In a real implementation, you'd use Windows API to get last input time
            
            # For now, we'll consider the user idle if the same app has been active
            # for more than the idle threshold without any window title changes
            if (self.current_session['app_start_time'] and 
                (current_time - self.current_session['app_start_time']).total_seconds() > self.idle_threshold):
                
                if not self.current_session['is_idle']:
                    self.current_session['is_idle'] = True
                    self.current_session['idle_start_time'] = current_time
                    self.logger.debug("User detected as idle")
            else:
                if self.current_session['is_idle']:
                    # User is back from idle
                    self._save_idle_period()
                    self.current_session['is_idle'] = False
                    self.current_session['idle_start_time'] = None
                    self.logger.debug("User back from idle")
                    
        except Exception as e:
            self.logger.error(f"Error checking idle state: {e}")
    
    def _handle_app_change(self, new_app: Optional[Dict], current_time: datetime):
        """Handle application change"""
        try:
            # Save previous app session
            if self.current_session['current_app']:
                self._save_app_session()
            
            # Update current session
            self.current_session['current_app'] = new_app
            self.current_session['app_start_time'] = current_time
            
            if new_app:
                self.logger.debug(f"App changed to: {new_app['app_name']} - {new_app['window_title'][:50]}")
            
        except Exception as e:
            self.logger.error(f"Error handling app change: {e}")
    
    def _save_app_session(self):
        """Save current app session to database"""
        try:
            if not self.current_session['current_app'] or not self.current_session['app_start_time']:
                return
            
            end_time = datetime.now()
            duration = (end_time - self.current_session['app_start_time']).total_seconds()
            
            # Don't save very short sessions (less than 5 seconds)
            if duration < 5:
                return
            
            app = self.current_session['current_app']
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO app_usage 
                    (date, app_name, window_title, category, start_time, end_time, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_session['app_start_time'].date().isoformat(),
                    app['app_name'],
                    app['window_title'][:500],  # Limit title length
                    app['category'],
                    self.current_session['app_start_time'].isoformat(),
                    end_time.isoformat(),
                    int(duration)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving app session: {e}")
    
    def _save_idle_period(self):
        """Save idle period to database"""
        try:
            if not self.current_session['idle_start_time']:
                return
            
            end_time = datetime.now()
            duration = (end_time - self.current_session['idle_start_time']).total_seconds()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO idle_periods 
                    (date, start_time, end_time, duration_seconds)
                    VALUES (?, ?, ?, ?)
                ''', (
                    self.current_session['idle_start_time'].date().isoformat(),
                    self.current_session['idle_start_time'].isoformat(),
                    end_time.isoformat(),
                    int(duration)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving idle period: {e}")
    
    def get_daily_summary(self, target_date: date = None) -> Dict:
        """Get daily activity summary"""
        if target_date is None:
            target_date = date.today()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get app usage for the day
                cursor.execute('''
                    SELECT app_name, category, SUM(duration_seconds) as total_duration,
                           COUNT(*) as session_count
                    FROM app_usage 
                    WHERE date = ?
                    GROUP BY app_name, category
                    ORDER BY total_duration DESC
                ''', (target_date.isoformat(),))
                
                app_usage = cursor.fetchall()
                
                # Get idle time for the day
                cursor.execute('''
                    SELECT SUM(duration_seconds) as total_idle
                    FROM idle_periods 
                    WHERE date = ?
                ''', (target_date.isoformat(),))
                
                idle_result = cursor.fetchone()
                total_idle = idle_result[0] if idle_result[0] else 0
                
                # Calculate summary
                total_active = sum(row[2] for row in app_usage)
                
                summary = {
                    'date': target_date.isoformat(),
                    'total_active_time': total_active,
                    'total_idle_time': total_idle,
                    'total_time': total_active + total_idle,
                    'apps_used': len(app_usage),
                    'app_usage': [],
                    'category_breakdown': defaultdict(int),
                    'productivity_score': 0.0
                }
                
                # Process app usage
                for app_name, category, duration, sessions in app_usage:
                    summary['app_usage'].append({
                        'app_name': app_name,
                        'category': category,
                        'duration_seconds': duration,
                        'duration_formatted': self._format_duration(duration),
                        'session_count': sessions,
                        'percentage': (duration / total_active * 100) if total_active > 0 else 0
                    })
                    
                    summary['category_breakdown'][category] += duration
                
                # Calculate productivity score
                summary['productivity_score'] = self._calculate_productivity_score(
                    dict(summary['category_breakdown']), total_active
                )
                
                # Get most used app and category
                if app_usage:
                    summary['most_used_app'] = app_usage[0][0]
                    
                if summary['category_breakdown']:
                    summary['most_used_category'] = max(
                        summary['category_breakdown'].items(),
                        key=lambda x: x[1]
                    )[0]
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Error getting daily summary: {e}")
            return {'error': str(e)}
    
    def get_weekly_summary(self, target_date: date = None) -> Dict:
        """Get weekly activity summary"""
        if target_date is None:
            target_date = date.today()
        
        # Get start of week (Monday)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get daily summaries for the week
                daily_summaries = []
                for i in range(7):
                    day = start_of_week + timedelta(days=i)
                    daily_summary = self.get_daily_summary(day)
                    daily_summaries.append(daily_summary)
                
                # Aggregate weekly data
                weekly_summary = {
                    'week_start': start_of_week.isoformat(),
                    'week_end': end_of_week.isoformat(),
                    'daily_summaries': daily_summaries,
                    'total_active_time': sum(day.get('total_active_time', 0) for day in daily_summaries),
                    'total_idle_time': sum(day.get('total_idle_time', 0) for day in daily_summaries),
                    'average_productivity_score': 0.0,
                    'most_productive_day': None,
                    'category_totals': defaultdict(int)
                }
                
                # Calculate averages and find most productive day
                valid_days = [day for day in daily_summaries if 'error' not in day]
                if valid_days:
                    weekly_summary['average_productivity_score'] = sum(
                        day.get('productivity_score', 0) for day in valid_days
                    ) / len(valid_days)
                    
                    # Find most productive day
                    most_productive = max(valid_days, key=lambda x: x.get('productivity_score', 0))
                    weekly_summary['most_productive_day'] = most_productive.get('date')
                    
                    # Aggregate category totals
                    for day in valid_days:
                        for category, duration in day.get('category_breakdown', {}).items():
                            weekly_summary['category_totals'][category] += duration
                
                return weekly_summary
                
        except Exception as e:
            self.logger.error(f"Error getting weekly summary: {e}")
            return {'error': str(e)}
    
    def get_app_statistics(self, days: int = 7) -> List[Dict]:
        """Get application usage statistics"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT app_name, category, 
                           SUM(duration_seconds) as total_duration,
                           COUNT(*) as total_sessions,
                           AVG(duration_seconds) as avg_session_duration,
                           COUNT(DISTINCT date) as days_used
                    FROM app_usage 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY app_name, category
                    ORDER BY total_duration DESC
                    LIMIT 20
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                results = cursor.fetchall()
                
                statistics = []
                for row in results:
                    statistics.append({
                        'app_name': row[0],
                        'category': row[1],
                        'total_duration': row[2],
                        'total_duration_formatted': self._format_duration(row[2]),
                        'total_sessions': row[3],
                        'avg_session_duration': round(row[4], 1),
                        'avg_session_formatted': self._format_duration(row[4]),
                        'days_used': row[5],
                        'usage_frequency': round(row[5] / days * 100, 1)  # Percentage of days used
                    })
                
                return statistics
                
        except Exception as e:
            self.logger.error(f"Error getting app statistics: {e}")
            return []
    
    def _calculate_productivity_score(self, category_breakdown: Dict[str, int], total_time: int) -> float:
        """Calculate productivity score based on app categories"""
        if total_time == 0:
            return 0.0
        
        # Productivity weights for different categories
        weights = {
            'productivity': 1.0,
            'development': 1.0,
            'communication': 0.7,
            'web_browsing': 0.3,
            'system': 0.5,
            'entertainment': 0.0,
            'other': 0.4
        }
        
        weighted_score = 0.0
        for category, duration in category_breakdown.items():
            weight = weights.get(category, 0.4)
            weighted_score += (duration / total_time) * weight
        
        return round(weighted_score * 100, 1)  # Convert to percentage
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _generate_daily_summary(self, target_date: date = None):
        """Generate and save daily summary"""
        if target_date is None:
            target_date = date.today()
        
        try:
            summary = self.get_daily_summary(target_date)
            
            if 'error' not in summary:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_summary 
                        (date, total_active_time, total_idle_time, most_used_app, 
                         most_used_category, productivity_score, apps_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        target_date.isoformat(),
                        summary.get('total_active_time', 0),
                        summary.get('total_idle_time', 0),
                        summary.get('most_used_app', ''),
                        summary.get('most_used_category', ''),
                        summary.get('productivity_score', 0.0),
                        summary.get('apps_used', 0)
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
    
    def get_productivity_insights(self) -> Dict:
        """Get productivity insights and recommendations"""
        try:
            today_summary = self.get_daily_summary()
            week_summary = self.get_weekly_summary()
            
            insights = {
                'productivity_trend': 'stable',
                'recommendations': [],
                'achievements': [],
                'focus_time': 0,
                'distraction_time': 0
            }
            
            # Calculate focus vs distraction time
            if 'category_breakdown' in today_summary:
                focus_categories = ['productivity', 'development']
                distraction_categories = ['entertainment', 'web_browsing']
                
                insights['focus_time'] = sum(
                    today_summary['category_breakdown'].get(cat, 0) 
                    for cat in focus_categories
                )
                
                insights['distraction_time'] = sum(
                    today_summary['category_breakdown'].get(cat, 0) 
                    for cat in distraction_categories
                )
            
            # Generate recommendations
            if today_summary.get('productivity_score', 0) < 50:
                insights['recommendations'].append(
                    "Consider reducing time spent on entertainment and social media"
                )
            
            if insights['distraction_time'] > insights['focus_time']:
                insights['recommendations'].append(
                    "Try to increase focus time by using productivity apps"
                )
            
            # Generate achievements
            if today_summary.get('productivity_score', 0) > 70:
                insights['achievements'].append("High productivity day!")
            
            if today_summary.get('total_active_time', 0) > 28800:  # 8 hours
                insights['achievements'].append("Full work day completed")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting productivity insights: {e}")
            return {'error': str(e)}
    
    def export_data(self, file_path: str, days: int = 30) -> bool:
        """Export activity data to JSON file"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'daily_summaries': [],
                'app_statistics': self.get_app_statistics(days)
            }
            
            # Get daily summaries
            current_date = start_date
            while current_date <= end_date:
                daily_summary = self.get_daily_summary(current_date)
                export_data['daily_summaries'].append(daily_summary)
                current_date += timedelta(days=1)
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Activity data exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Remove activity data older than specified days"""
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records to be deleted
                cursor.execute('SELECT COUNT(*) FROM app_usage WHERE date < ?', (cutoff_date.isoformat(),))
                app_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM idle_periods WHERE date < ?', (cutoff_date.isoformat(),))
                idle_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM daily_summary WHERE date < ?', (cutoff_date.isoformat(),))
                summary_count = cursor.fetchone()[0]
                
                # Delete old records
                cursor.execute('DELETE FROM app_usage WHERE date < ?', (cutoff_date.isoformat(),))
                cursor.execute('DELETE FROM idle_periods WHERE date < ?', (cutoff_date.isoformat(),))
                cursor.execute('DELETE FROM daily_summary WHERE date < ?', (cutoff_date.isoformat(),))
                
                conn.commit()
                
                total_deleted = app_count + idle_count + summary_count
                self.logger.info(f"Cleaned up {total_deleted} old activity records")
                
                return total_deleted
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            return 0