import sqlite3
import config
from datetime import datetime

def _connect():
    conn = sqlite3.connect(config.DB_FILE)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        rssi INTEGER,
        room TEXT
    )
    """)
    return conn

def log_event(event_type, rssi, room=None):
    conn = _connect()
    conn.execute(
        "INSERT INTO events (timestamp, event_type, rssi, room) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), event_type, rssi, room)
    )
    conn.commit()
    conn.close()

def get_recent_events(limit=50):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows
