"""
========================================================
Database Module
--------------------------------------------------------
This module manages the SQLite database used in the
Driver Drowsiness Detection System.

Functions of this module:
1. Store latest driver drowsiness status
2. Store admin messages / feedback
3. Retrieve stored data for dashboard display

Database File:
driver_data.db

Tables:
1. driver_status
2. admin_messages
========================================================
"""

import sqlite3
import os
import time

# -------------------------------------------------------
# Database file location
# -------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "driver_data.db")


# -------------------------------------------------------
# Initialize Database
# -------------------------------------------------------

def init_db():
    """
    Create required tables if they do not exist.
    """

    with sqlite3.connect(DB_PATH) as conn:

        # Driver status table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS driver_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            status TEXT NOT NULL,
            drowsiness_score INTEGER NOT NULL,
            ear REAL NOT NULL,
            mar REAL NOT NULL,
            blink_count INTEGER NOT NULL,
            yawn_count INTEGER NOT NULL,
            alert_count INTEGER NOT NULL
        )
        """)

        # Admin messages table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


# -------------------------------------------------------
# Insert Driver Status
# -------------------------------------------------------

def insert_status(status, drowsiness_score, ear, mar,
                  blink_count, yawn_count, alert_count):
    """
    Save latest driver detection result.

    This system keeps only the latest record for simplicity.
    """

    with sqlite3.connect(DB_PATH) as conn:

        # Insert new record (keep last 200 rows for history, never wipe all)
        conn.execute("""
        INSERT INTO driver_status
        (timestamp, status, drowsiness_score, ear, mar,
         blink_count, yawn_count, alert_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            time.time(),
            status,
            drowsiness_score,
            ear,
            mar,
            blink_count,
            yawn_count,
            alert_count
        ))

        # Keep only the latest 200 rows so the DB doesn't grow forever
        conn.execute("""
        DELETE FROM driver_status
        WHERE id NOT IN (
            SELECT id FROM driver_status
            ORDER BY timestamp DESC
            LIMIT 200
        )
        """)

        conn.commit()


# -------------------------------------------------------
# Get Latest Driver Status
# -------------------------------------------------------

def get_latest_status():
    """
    Retrieve latest stored driver status.
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
        SELECT * FROM driver_status
        ORDER BY timestamp DESC
        LIMIT 1
        """).fetchone()

        if row:
            return dict(row)

        return None


# -------------------------------------------------------
# Insert Admin Message
# -------------------------------------------------------

def insert_admin_message(message):
    """
    Store a message sent by admin with real local timestamp.
    Uses Python datetime.now() instead of SQLite CURRENT_TIMESTAMP
    because SQLite's CURRENT_TIMESTAMP is always UTC — using Python
    ensures the stored time matches the server's local timezone.
    """
    from datetime import datetime

    local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
        INSERT INTO admin_messages (message, timestamp)
        VALUES (?, ?)
        """, (message, local_ts))

        conn.commit()


# -------------------------------------------------------
# Get All Admin Messages
# -------------------------------------------------------

def get_all_admin_messages():
    """
    Return all admin messages ordered by newest first.
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
        SELECT message, timestamp
        FROM admin_messages
        ORDER BY timestamp DESC
        """).fetchall()

        return [dict(row) for row in rows]


# -------------------------------------------------------
# Initialize database automatically
# -------------------------------------------------------

init_db()