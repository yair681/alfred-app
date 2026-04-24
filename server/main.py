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


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    reply = handle_message(req.user_id, req.message)
    return ChatResponse(reply=reply)


@app.get("/health")
async def health():
    return {"status": "ok", "version": 1, "bot": "אלפרד"}
