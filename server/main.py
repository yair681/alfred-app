from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import database
from agent import handle_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "alfred_user"
    image_base64: str | None = None
    image_mime_type: str = "image/jpeg"


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    reply = handle_message(req.user_id, req.message, req.image_base64, req.image_mime_type)
    return ChatResponse(reply=reply)


@app.get("/notifications/{user_id}")
async def get_notifications(user_id: str):
    from tools.reminders import pop_pending
    pending = pop_pending(user_id)
    return {"notifications": pending}


@app.get("/test-reminder/{user_id}")
async def test_reminder(user_id: str):
    import database
    database.add_notification(user_id, "🔔 בדיקה — התזכורות עובדות!")
    return {"status": "ok", "message": "notification added"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": 1, "bot": "אלפרד"}
