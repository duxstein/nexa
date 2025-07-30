#!/usr/bin/env python3
"""
Task Manager for NEXA
Handles reminders, to-dos, and calendar integration
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Task:
    id: Optional[int] = None
    description: str = ""
    due_date: Optional[datetime] = None
    created_date: datetime = None
    completed_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: str = "general"
    notes: str = ""
    reminder_time: Optional[datetime] = None
    recurring: bool = False
    recurring_pattern: Optional[str] = None  # daily, weekly, monthly
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()

class TaskManager:
    """Task and reminder management system for NEXA"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.logger = logging.getLogger(__name__)
        self.conn = db_connection
        self.tasks: List[Task] = []
        
        # Load existing tasks
        self._load_tasks()
        
        # Start reminder checking thread
        self.reminder_thread = threading.Thread(target=self._check_reminders, daemon=True)
        self.reminder_thread.start()
        
        # Callback for reminder notifications
        self.reminder_callback = None
    

    
    def _load_tasks(self):
        """Load tasks from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE status != ?', (TaskStatus.COMPLETED.value,))
            
            rows = cursor.fetchall()
            self.tasks = []
            
            for row in rows:
                task = Task(
                    id=row[0],
                    description=row[1],
                    due_date=datetime.fromisoformat(row[2]) if row[2] else None,
                    created_date=datetime.fromisoformat(row[3]),
                    completed_date=datetime.fromisoformat(row[4]) if row[4] else None,
                    status=TaskStatus(row[5]),
                    priority=TaskPriority(row[6]),
                    category=row[7],
                    notes=row[8] or "",
                    reminder_time=datetime.fromisoformat(row[9]) if row[9] else None,
                    recurring=bool(row[10]),
                    recurring_pattern=row[11]
                )
                self.tasks.append(task)
            
            self.logger.info(f"Loaded {len(self.tasks)} tasks from database")
            
        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")
    
    def add_task(self, description: str, due_date: Optional[datetime] = None, 
                 priority: TaskPriority = TaskPriority.MEDIUM, 
                 category: str = "general", notes: str = "") -> Task:
        """Add a new task"""
        task = Task(
            description=description,
            due_date=due_date,
            priority=priority,
            category=category,
            notes=notes
        )
        
        try:
            # Save to database
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (description, due_date, created_date, status, priority, category, notes, recurring)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.description,
                task.due_date.isoformat() if task.due_date else None,
                task.created_date.isoformat(),
                task.status.value,
                task.priority.value,
                task.category,
                task.notes,
                task.recurring
            ))
            
            task.id = cursor.lastrowid
            self.conn.commit()
            
            # Add to memory
            self.tasks.append(task)
            
            self.logger.info(f"Added task: {task.description}")
            return task
            
        except Exception as e:
            self.logger.error(f"Error adding task: {e}")
            raise
    
    def add_reminder(self, description: str, reminder_time_str: str) -> Task:
        """Add a reminder with specific time"""
        try:
            # Parse time string
            reminder_time = self._parse_time_string(reminder_time_str)
            
            task = Task(
                description=description,
                due_date=reminder_time,
                reminder_time=reminder_time,
                priority=TaskPriority.HIGH,
                category="reminder"
            )
            
            # Save to database
            cursor = self.database.get_cursor()
            cursor.execute('''
                INSERT INTO tasks (description, due_date, created_date, status, priority, category, reminder_time, recurring)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.description,
                task.due_date.isoformat() if task.due_date else None,
                task.created_date.isoformat(),
                task.status.value,
                task.priority.value,
                task.category,
                task.reminder_time.isoformat() if task.reminder_time else None,
                task.recurring
            ))
            
            task.id = cursor.lastrowid
            self.database.commit()
            
            # Add to memory
            self.tasks.append(task)
            
            self.logger.info(f"Added reminder: {task.description} at {reminder_time}")
            return task
            
        except Exception as e:
            self.logger.error(f"Error adding reminder: {e}")
            raise
    
    def _parse_time_string(self, time_str: str) -> datetime:
        """Parse time string into datetime object"""
        now = datetime.now()
        time_str = time_str.lower().strip()
        
        # Handle relative times
        if 'in' in time_str:
            # "in 30 minutes", "in 2 hours"
            parts = time_str.split()
            if len(parts) >= 3:
                try:
                    amount = int(parts[1])
                    unit = parts[2]
                    
                    if 'minute' in unit:
                        return now + timedelta(minutes=amount)
                    elif 'hour' in unit:
                        return now + timedelta(hours=amount)
                    elif 'day' in unit:
                        return now + timedelta(days=amount)
                except ValueError:
                    pass
        
        # Handle specific times
        # "5 PM", "17:30", "5:30 PM"
        time_formats = [
            "%I %p",      # "5 PM"
            "%I:%M %p",   # "5:30 PM"
            "%H:%M",      # "17:30"
            "%H",         # "17"
        ]
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                reminder_datetime = datetime.combine(now.date(), parsed_time)
                
                # If time has passed today, schedule for tomorrow
                if reminder_datetime <= now:
                    reminder_datetime += timedelta(days=1)
                
                return reminder_datetime
            except ValueError:
                continue
        
        # Default: 1 hour from now
        return now + timedelta(hours=1)
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_date = datetime.now()
            
            # Update database
            cursor = self.database.get_cursor()
            cursor.execute('''
                UPDATE tasks SET status = ?, completed_date = ? WHERE id = ?
            ''', (task.status.value, task.completed_date.isoformat(), task.id))
            
            self.database.commit()
            
            # Remove from active tasks
            self.tasks = [t for t in self.tasks if t.id != task_id]
            
            self.logger.info(f"Completed task: {task.description}")
            
            # Handle recurring tasks
            if task.recurring and task.recurring_pattern:
                self._create_recurring_task(task)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing task: {e}")
            return False
    
    def _create_recurring_task(self, original_task: Task):
        """Create next occurrence of recurring task"""
        try:
            next_due_date = None
            
            if original_task.recurring_pattern == "daily":
                next_due_date = original_task.due_date + timedelta(days=1)
            elif original_task.recurring_pattern == "weekly":
                next_due_date = original_task.due_date + timedelta(weeks=1)
            elif original_task.recurring_pattern == "monthly":
                next_due_date = original_task.due_date + timedelta(days=30)
            
            if next_due_date:
                new_task = Task(
                    description=original_task.description,
                    due_date=next_due_date,
                    priority=original_task.priority,
                    category=original_task.category,
                    notes=original_task.notes,
                    reminder_time=next_due_date,
                    recurring=True,
                    recurring_pattern=original_task.recurring_pattern
                )
                
                # Save new task
                cursor = self.database.get_cursor()
                cursor.execute('''
                    INSERT INTO tasks (description, due_date, created_date, status, priority, category, notes, reminder_time, recurring, recurring_pattern)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_task.description,
                    new_task.due_date.isoformat(),
                    new_task.created_date.isoformat(),
                    new_task.status.value,
                    new_task.priority.value,
                    new_task.category,
                    new_task.notes,
                    new_task.reminder_time.isoformat(),
                    new_task.recurring,
                    new_task.recurring_pattern
                ))
                
                new_task.id = cursor.lastrowid
                self.database.commit()
                self.tasks.append(new_task)
                
                self.logger.info(f"Created recurring task: {new_task.description}")
                
        except Exception as e:
            self.logger.error(f"Error creating recurring task: {e}")
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        try:
            cursor = self.database.get_cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            self.database.commit()
            
            # Remove from memory
            self.tasks = [t for t in self.tasks if t.id != task_id]
            
            self.logger.info(f"Deleted task ID: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting task: {e}")
            return False
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks"""
        pending_tasks = [t for t in self.tasks if t.status == TaskStatus.PENDING]
        
        # Sort by priority and due date
        pending_tasks.sort(key=lambda t: (
            t.priority.value,
            t.due_date if t.due_date else datetime.max
        ))
        
        return [self._task_to_dict(task) for task in pending_tasks]
    
    def get_tasks_by_category(self, category: str) -> List[Dict]:
        """Get tasks by category"""
        category_tasks = [t for t in self.tasks if t.category == category]
        return [self._task_to_dict(task) for task in category_tasks]
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Get overdue tasks"""
        now = datetime.now()
        overdue_tasks = [
            t for t in self.tasks 
            if t.status == TaskStatus.PENDING and t.due_date and t.due_date < now
        ]
        
        # Update status to overdue
        for task in overdue_tasks:
            task.status = TaskStatus.OVERDUE
            self._update_task_in_db(task)
        
        return [self._task_to_dict(task) for task in overdue_tasks]
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def search_tasks(self, query: str) -> List[Dict]:
        """Search tasks by description"""
        query = query.lower()
        matching_tasks = [
            t for t in self.tasks 
            if query in t.description.lower() or query in t.notes.lower()
        ]
        return [self._task_to_dict(task) for task in matching_tasks]
    
    def _task_to_dict(self, task: Task) -> Dict:
        """Convert task to dictionary"""
        return {
            'id': task.id,
            'description': task.description,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_date': task.created_date.isoformat(),
            'status': task.status.value,
            'priority': task.priority.value,
            'category': task.category,
            'notes': task.notes,
            'reminder_time': task.reminder_time.isoformat() if task.reminder_time else None,
            'recurring': task.recurring
        }
    
    def _update_task_in_db(self, task: Task):
        """Update task in database"""
        try:
            cursor = self.database.get_cursor()
            cursor.execute('''
                UPDATE tasks SET 
                    description = ?, due_date = ?, status = ?, priority = ?, 
                    category = ?, notes = ?, reminder_time = ?, recurring = ?, recurring_pattern = ?
                WHERE id = ?
            ''', (
                task.description,
                task.due_date.isoformat() if task.due_date else None,
                task.status.value,
                task.priority.value,
                task.category,
                task.notes,
                task.reminder_time.isoformat() if task.reminder_time else None,
                task.recurring,
                task.recurring_pattern,
                task.id
            ))
            self.database.commit()
        except Exception as e:
            self.logger.error(f"Error updating task in database: {e}")
    
    def _check_reminders(self):
        """Background thread to check for due reminders"""
        while True:
            try:
                now = datetime.now()
                
                for task in self.tasks:
                    if (task.reminder_time and 
                        task.status == TaskStatus.PENDING and 
                        task.reminder_time <= now):
                        
                        # Trigger reminder
                        self._trigger_reminder(task)
                        
                        # Clear reminder time to avoid repeated notifications
                        task.reminder_time = None
                        self._update_task_in_db(task)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error checking reminders: {e}")
                time.sleep(60)
    
    def _trigger_reminder(self, task: Task):
        """Trigger reminder notification"""
        reminder_message = f"Reminder: {task.description}"
        
        if self.reminder_callback:
            self.reminder_callback(reminder_message)
        
        self.logger.info(f"Triggered reminder: {task.description}")
    
    def set_reminder_callback(self, callback):
        """Set callback for reminder notifications"""
        self.reminder_callback = callback
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Get task statistics"""
        stats = {
            'total_tasks': len(self.tasks),
            'pending': len([t for t in self.tasks if t.status == TaskStatus.PENDING]),
            'overdue': len([t for t in self.tasks if t.status == TaskStatus.OVERDUE]),
            'high_priority': len([t for t in self.tasks if t.priority == TaskPriority.HIGH]),
            'urgent': len([t for t in self.tasks if t.priority == TaskPriority.URGENT])
        }
        
        # Get completed tasks from database
        try:
            cursor = self.database.get_cursor()
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', (TaskStatus.COMPLETED.value,))
            stats['completed'] = cursor.fetchone()[0]
        except:
            stats['completed'] = 0
        
        return stats
    
    def save_tasks(self):
        """Save all tasks to database (called on shutdown)"""
        try:
            for task in self.tasks:
                self._update_task_in_db(task)
            self.logger.info("All tasks saved to database")
        except Exception as e:
            self.logger.error(f"Error saving tasks: {e}")