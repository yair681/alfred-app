import json

from groq import Groq, BadRequestError

import database
from config import GROQ_API_KEY, LLM_MODEL, MAX_HISTORY
from prompt import build_system_prompt
from tools import TOOL_REGISTRY
import tools.reminders  # registers reminder tools
import tools.google_calendar  # registers calendar tools
import tools.gmail  # registers gmail tools

FRAMEWORK_INJECTED_USER_ID = {"create_reminder", "list_reminders", "cancel_reminder"}

_client = Groq(api_key=GROQ_API_KEY)


def _run_tool(tool_name: str, tool_input: dict, user_id: str) -> str:
    if tool_name not in TOOL_REGISTRY:
        return f"כלי '{tool_name}' לא קיים."
    args = dict(tool_input)
    if tool_name in FRAMEWORK_INJECTED_USER_ID:
        args["user_id"] = user_id
    try:
        return str(TOOL_REGISTRY[tool_name]["fn"](**args))
    except Exception as e:
        return f"שגיאה בהרצת {tool_name}: {e}"


VISION_MODEL = "llama-3.2-11b-vision-preview"


def _build_user_content(message: str, image_base64: str | None, image_mime_type: str) -> list | str:
    if not image_base64:
        return message
    return [
        {"type": "text", "text": message or "מה יש בתמונה?"},
        {"type": "image_url", "image_url": {"url": f"data:{image_mime_type};base64,{image_base64}"}},
    ]


def handle_message(user_id: str, message: str, image_base64: str | None = None, image_mime_type: str = "image/jpeg") -> str:
    from tools.reminders import pop_pending
    pending = pop_pending(user_id)
    if pending:
        reminder_text = " | ".join(pending)
        database.append(user_id, "assistant", f"🔔 תזכורת: {reminder_text}")

    display_message = message or "[תמונה]"
    database.append(user_id, "user", display_message)
    history = database.tail(user_id, MAX_HISTORY)

    system_prompt = build_system_prompt(TOOL_REGISTRY)
    user_content = _build_user_content(message, image_base64, image_mime_type)
    history_with_image = history[:-1] + [{"role": "user", "content": user_content}]
    messages = [{"role": "system", "content": system_prompt}] + history_with_image

    model = VISION_MODEL if image_base64 else LLM_MODEL
    tools_schema = [] if image_base64 else [td["schema"] for td in TOOL_REGISTRY.values()]

    for _ in range(5):
        kwargs = {"model": model, "messages": messages}
        if tools_schema:
            kwargs["tools"] = [{"type": "function", "function": s} for s in tools_schema]
            kwargs["tool_choice"] = "auto"

        try:
            response = _client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            if "tool_use_failed" in str(e):
                # Llama 4 on Groq sometimes generates text instead of valid tool-call JSON.
                # Retry without tool schema so Groq doesn't try to parse it as a function call.
                fallback = {k: v for k, v in kwargs.items() if k not in ("tools", "tool_choice")}
                response = _client.chat.completions.create(**fallback)
            else:
                raise
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            assistant_msg = {"role": "assistant", "content": choice.message.content or "", "tool_calls": []}
            tool_results = []
            for tc in choice.message.tool_calls:
                tool_input = json.loads(tc.function.arguments or "{}")
                result = _run_tool(tc.function.name, tool_input, user_id)
                assistant_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                })
                tool_results.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            messages.append(assistant_msg)
            messages.extend(tool_results)
        else:
            reply = choice.message.content or "סליחה, לא הצלחתי לענות."
            database.append(user_id, "assistant", reply)
            return reply

    reply = "סליחה, הגעתי למגבלת עיבוד. נסה שוב."
    database.append(user_id, "assistant", reply)
    return reply
