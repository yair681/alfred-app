import sqlite3
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH


def _connect() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_ids (
                message_id TEXT PRIMARY KEY
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def append(user_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.utcnow().isoformat()),
        )


def add_notification(user_id: str, message: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO notifications (user_id, message, created_at) VALUES (?, ?, ?)",
            (user_id, message, datetime.utcnow().isoformat()),
        )


def pop_notifications(user_id: str) -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, message FROM notifications WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        if rows:
            ids = ",".join(str(r[0]) for r in rows)
            conn.execute(f"DELETE FROM notifications WHERE id IN ({ids})")
    return [r[1] for r in rows]


def tail(user_id: str, n: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, n),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]
