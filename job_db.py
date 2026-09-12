#!/usr/bin/env python3
"""
Job Hunter SQLite Database Engine.
Stores and tracks job applications across the Kanban lifecycle.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "job_hunter.db"

KANBAN_STAGES = [
    "wishlist",
    "applied",
    "screening",
    "tech_test",
    "user_interview",
    "offering",
    "rejected",
    "withdrawn"
]

STAGE_EMOJIS = {
    "wishlist": "📋",
    "applied": "📨",
    "screening": "📞",
    "tech_test": "💻",
    "user_interview": "🤝",
    "offering": "🎉",
    "rejected": "❌",
    "withdrawn": "⏹️"
}

STAGE_LABELS = {
    "wishlist": "Wishlist (Diincar)",
    "applied": "Sudah Dilamar (Applied)",
    "screening": "Screening HR",
    "tech_test": "Technical Test / Challenge",
    "user_interview": "Interview User / Lead",
    "offering": "Offering Letter 🎉",
    "rejected": "Ditolak (Rejected)",
    "withdrawn": "Dibatalkan (Withdrawn)"
}

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT DEFAULT 'Remote',
                salary TEXT DEFAULT 'Kompetitif',
                job_url TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'wishlist',
                applied_date TEXT,
                next_schedule TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

def add_application(
    company: str,
    role: str,
    location: str = "Remote",
    salary: str = "Kompetitif",
    job_url: str = "",
    status: str = "wishlist",
    applied_date: Optional[str] = None,
    next_schedule: str = "",
    notes: str = ""
) -> int:
    status = status.lower()
    if status not in KANBAN_STAGES:
        status = "wishlist"
        
    if not applied_date and status in ("applied", "screening", "tech_test", "user_interview", "offering"):
        applied_date = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO job_applications (
                company, role, location, salary, job_url, status, applied_date, next_schedule, notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (company.strip(), role.strip(), location.strip(), salary.strip(), job_url.strip(), status, applied_date, next_schedule, notes))
        conn.commit()
        return cur.lastrowid

def update_application_status(
    app_id: int,
    new_status: str,
    next_schedule: Optional[str] = None,
    notes: Optional[str] = None
) -> bool:
    new_status = new_status.lower()
    if new_status not in KANBAN_STAGES:
        return False

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM job_applications WHERE id = ?", (app_id,))
        row = cur.fetchone()
        if not row:
            return False

        updated_schedule = next_schedule if next_schedule is not None else row["next_schedule"]
        updated_notes = (f"{row['notes']}\n{notes}".strip()) if notes else row["notes"]
        applied_date = row["applied_date"]
        
        if not applied_date and new_status != "wishlist":
            applied_date = datetime.now().strftime("%Y-%m-%d")

        cur.execute("""
            UPDATE job_applications
            SET status = ?, next_schedule = ?, notes = ?, applied_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, updated_schedule, updated_notes, applied_date, app_id))
        conn.commit()
        return cur.rowcount > 0

def get_all_applications(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if status_filter and status_filter.lower() in KANBAN_STAGES:
            cur = conn.execute("SELECT * FROM job_applications WHERE status = ? ORDER BY id DESC", (status_filter.lower(),))
        else:
            cur = conn.execute("SELECT * FROM job_applications ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

def get_application_by_id(app_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM job_applications WHERE id = ?", (app_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def delete_application(app_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM job_applications WHERE id = ?", (app_id,))
        conn.commit()
        return cur.rowcount > 0

if __name__ == "__main__":
    init_db()
    print("Job database initialized at:", DB_PATH)
