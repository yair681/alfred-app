from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import DATABASE_PATH
from tools import TOOL_REGISTRY

_jobstore_url = f"sqlite:///{DATABASE_PATH}"
_scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=_jobstore_url)}
)
_scheduler.start()

_pending: dict[str, list] = {}


def _fire_reminder(user_id: str, message: str) -> None:
    if user_id not in _pending:
        _pending[user_id] = []
    _pending[user_id].append(message)


def create_reminder(user_id: str, remind_at_iso: str, message: str) -> str:
    run_time = datetime.fromisoformat(remind_at_iso)
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
    return _pending.pop(user_id, [])


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
