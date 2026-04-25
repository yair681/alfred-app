import base64
import email as email_lib
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
    return build("gmail", "v1", credentials=creds)

def _extract_body(payload: dict) -> str:
    import base64
    import re

    def decode(data: str) -> str:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    def strip_html(text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&[a-z]+;", "", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    def find_text(part: dict) -> str:
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return decode(part["body"]["data"])
        if mime == "text/html" and part.get("body", {}).get("data"):
            return strip_html(decode(part["body"]["data"]))
        for sub in part.get("parts", []):
            result = find_text(sub)
            if result:
                return result
        return ""

    text = find_text(payload)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:600]


def search_emails(query: str, max_results: int = 5) -> str:
    svc = _service()
    result = svc.users().messages().list(userId="me", q=query, maxResults=int(max_results)).execute()
    messages = result.get("messages", [])
    if not messages:
        return "לא נמצאו מיילים."
    lines = []
    for m in messages:
        msg = svc.users().messages().get(userId="me", id=m["id"], format="full",
              metadataHeaders=["Subject", "From", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        body = _extract_body(msg["payload"])
        lines.append(
            f"--- מייל ---\n"
            f"נושא: {headers.get('Subject','ללא נושא')}\n"
            f"מ: {headers.get('From','')}\n"
            f"תאריך: {headers.get('Date','')}\n"
            f"תוכן: {body or '(ריק)'}"
        )
    return "\n\n".join(lines)

def get_email(message_id: str) -> str:
    svc = _service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = ""
    if "parts" in msg["payload"]:
        for part in msg["payload"]["parts"]:
            if part["mimeType"] == "text/plain":
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
    elif "body" in msg["payload"] and msg["payload"]["body"].get("data"):
        body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8", errors="ignore")
    return f"נושא: {headers.get('Subject')}\nמ: {headers.get('From')}\n\n{body[:1000]}"

def send_email(to: str, subject: str, body: str) -> str:
    import email.mime.text
    svc = _service()
    msg = email.mime.text.MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"מייל נשלח ל-{to}"

from tools import TOOL_REGISTRY

TOOL_REGISTRY["search_emails"] = {
    "schema": {
        "name": "search_emails",
        "description": "מחפש מיילים ב-Gmail לפי שאילתה",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "שאילתת חיפוש (למשל 'from:yosi' או 'subject:פגישה'). מחזיר עד 5 תוצאות."},
            },
            "required": ["query"],
        },
    },
    "fn": search_emails,
}

TOOL_REGISTRY["get_email"] = {
    "schema": {
        "name": "get_email",
        "description": "קורא מייל מלא לפי מזהה",
        "parameters": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "מזהה המייל"},
            },
            "required": ["message_id"],
        },
    },
    "fn": get_email,
}

TOOL_REGISTRY["send_email"] = {
    "schema": {
        "name": "send_email",
        "description": "שולח מייל מחשבון Gmail של המשתמש",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "כתובת המייל של הנמען"},
                "subject": {"type": "string", "description": "נושא המייל"},
                "body": {"type": "string", "description": "תוכן המייל"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    "fn": send_email,
}
