import json

from groq import Groq

import database
from config import GROQ_API_KEY, LLM_MODEL, MAX_HISTORY
from prompt import build_system_prompt
from tools import TOOL_REGISTRY
import tools.reminders  # registers reminder tools

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


def handle_message(user_id: str, message: str) -> str:
    from tools.reminders import pop_pending
    pending = pop_pending(user_id)
    if pending:
        reminder_text = " | ".join(pending)
        database.append(user_id, "assistant", f"🔔 תזכורת: {reminder_text}")

    database.append(user_id, "user", message)
    history = database.tail(user_id, MAX_HISTORY)

    system_prompt = build_system_prompt(TOOL_REGISTRY)
    messages = [{"role": "system", "content": system_prompt}] + history

    tools_schema = [td["schema"] for td in TOOL_REGISTRY.values()]

    for _ in range(5):
        kwargs = {"model": LLM_MODEL, "messages": messages}
        if tools_schema:
            kwargs["tools"] = [{"type": "function", "function": s} for s in tools_schema]
            kwargs["tool_choice"] = "auto"

        response = _client.chat.completions.create(**kwargs)
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
