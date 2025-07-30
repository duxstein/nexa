#!/usr/bin/env python3
"""
Database Manager for NEXA
Handles SQLite database connections and operations.
"""

import sqlite3
import logging
from pathlib import Path

class Database:
    """Manages the connection to the SQLite database."""

    def __init__(self, db_path: str = 'nexa_data.db'):
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()

    def _connect(self):
        """Establishes a connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.logger.info(f"Successfully connected to database at {self.db_path}")
            self._create_tables()
        except sqlite3.Error as e:
            self.logger.error(f"Database connection failed: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Returns the current database connection."""
        return self.conn

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed.")

    def _create_tables(self):
        """Creates the necessary tables if they don't exist."""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            # Task Manager Tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    due_date TEXT,
                    created_date TEXT NOT NULL,
                    completed_date TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    category TEXT NOT NULL,
                    notes TEXT,
                    reminder_time TEXT,
                    recurring BOOLEAN,
                    recurring_pattern TEXT
                )
            ''')
            # Activity Tracker Tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    duration REAL,
                    category TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS idle_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    duration_seconds REAL NOT NULL
                )
            ''')
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

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(app_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(date)')

            self.conn.commit()
            self.logger.info("Database tables created or verified.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")