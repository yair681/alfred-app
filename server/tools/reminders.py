from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

import database
from config import DATABASE_PATH
from tools import TOOL_REGISTRY

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

_jobstore_url = f"sqlite:///{DATABASE_PATH}"
_scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=_jobstore_url)},
    timezone="Asia/Jerusalem",
    job_defaults={"misfire_grace_time": 3600},
)
_scheduler.start()


def _fire_reminder(user_id: str, message: str) -> None:
    database.add_notification(user_id, message)


def create_reminder(user_id: str, remind_at_iso: str, message: str) -> str:
    run_time = datetime.fromisoformat(remind_at_iso)
    if run_time.tzinfo is None:
        run_time = run_time.replace(tzinfo=ISRAEL_TZ)
    job = _scheduler.add_job(
        _fire_reminder,
        "date",
        run_date=run_time,
        args=[user_id, message],
    )
    return f"תזכורת נקבעה ל-{run_time.strftime('%d/%m/%Y %H:%M')} — {message} (מזהה: {job.id})"


def list_reminders(user_id: str) -> str:
    jobs = _scheduler.get_jobs()
    user_jobs = [j for j in jobs if j.args and j.args[0] == user_id]
    if not user_jobs:
        return "אין תזכורות פעילות."
    lines = [f"- {j.next_run_time.strftime('%d/%m/%Y %H:%M')}: {j.args[1]} (מזהה: {j.id})" for j in user_jobs]
    return "\n".join(lines)


def cancel_reminder(reminder_id: str) -> str:
    try:
        _scheduler.remove_job(reminder_id)
        return f"תזכורת {reminder_id} בוטלה."
    except Exception:
        return f"לא נמצאה תזכורת עם מזהה {reminder_id}."


def pop_pending(user_id: str) -> list[str]:
    return database.pop_notifications(user_id)


TOOL_REGISTRY["create_reminder"] = {
    "schema": {
        "name": "create_reminder",
        "description": "קובע תזכורת למשתמש בזמן מסוים",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "מזהה המשתמש — ימולא על ידי המערכת"},
                "remind_at_iso": {"type": "string", "description": "זמן התזכורת בפורמט ISO 8601"},
                "message": {"type": "string", "description": "תוכן התזכורת"},
            },
            "required": ["user_id", "remind_at_iso", "message"],
        },
    },
    "fn": create_reminder,
}

TOOL_REGISTRY["list_reminders"] = {
    "schema": {
        "name": "list_reminders",
        "description": "מציג את כל התזכורות הפעילות של המשתמש",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "מזהה המשתמש — ימולא על ידי המערכת"},
            },
            "required": ["user_id"],
        },
    },
    "fn": list_reminders,
}

TOOL_REGISTRY["cancel_reminder"] = {
    "schema": {
        "name": "cancel_reminder",
        "description": "מבטל תזכורת לפי מזהה",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder_id": {"type": "string", "description": "מזהה התזכורת לביטול"},
            },
            "required": ["reminder_id"],
        },
    },
    "fn": cancel_reminder,
}
