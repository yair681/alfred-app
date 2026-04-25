from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

def _service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("calendar", "v3", credentials=creds)

def list_events(time_min_iso: str, time_max_iso: str) -> str:
    svc = _service()
    result = svc.events().list(
        calendarId="primary",
        timeMin=time_min_iso,
        timeMax=time_max_iso,
        singleEvents=True,
        orderBy="startTime",
        maxResults=10,
    ).execute()
    events = result.get("items", [])
    if not events:
        return "אין אירועים בטווח הזמן שביקשת."
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        lines.append(f"- {e.get('summary', 'ללא כותרת')} | {start}")
    return "\n".join(lines)

def create_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> str:
    svc = _service()
    event = svc.events().insert(calendarId="primary", body={
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }).execute()
    return f"אירוע נוצר: {event.get('summary')} ב-{start_iso}"

def delete_event(event_id: str) -> str:
    _service().events().delete(calendarId="primary", eventId=event_id).execute()
    return f"אירוע {event_id} נמחק."

from tools import TOOL_REGISTRY

TOOL_REGISTRY["list_calendar_events"] = {
    "schema": {
        "name": "list_calendar_events",
        "description": "מציג אירועים מיומן גוגל בין שני תאריכים",
        "parameters": {
            "type": "object",
            "properties": {
                "time_min_iso": {"type": "string", "description": "זמן התחלה ISO 8601 עם timezone (למשל 2026-04-25T00:00:00+03:00)"},
                "time_max_iso": {"type": "string", "description": "זמן סיום ISO 8601 עם timezone"},
            },
            "required": ["time_min_iso", "time_max_iso"],
        },
    },
    "fn": list_events,
}

TOOL_REGISTRY["create_calendar_event"] = {
    "schema": {
        "name": "create_calendar_event",
        "description": "יוצר אירוע חדש ביומן גוגל",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "כותרת האירוע"},
                "start_iso": {"type": "string", "description": "זמן התחלה ISO 8601"},
                "end_iso": {"type": "string", "description": "זמן סיום ISO 8601"},
                "description": {"type": "string", "description": "תיאור האירוע (אופציונלי)"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    "fn": create_event,
}

TOOL_REGISTRY["delete_calendar_event"] = {
    "schema": {
        "name": "delete_calendar_event",
        "description": "מוחק אירוע מיומן גוגל לפי מזהה",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "מזהה האירוע"},
            },
            "required": ["event_id"],
        },
    },
    "fn": delete_event,
}
