from config import SPEC


def _tools_section(tool_registry: dict) -> str:
    if not tool_registry:
        return "אין לך כלים חיצוניים כרגע. ענה מהידע שלך בלבד."
    lines = ["יש לך הכלים הבאים:"]
    for name, td in tool_registry.items():
        desc = td["schema"].get("description", "")
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)


def build_system_prompt(tool_registry: dict) -> str:
    identity = SPEC["identity"]
    name = identity["name"]
    tone = identity["tone_description"]
    greeting = identity["greeting_example"]

    prompt = f"""אתה {name}, עוזר אישי חכם ומצחיק.

אופי: {tone}
כשמישהו אומר לך "היי", ענה: "{greeting}"

כללי תקשורת:
- ענה בעברית תמיד, אלא אם המשתמש כותב באנגלית
- תשובות באורך בינוני — לא קצרות מדי ולא ארוכות מדי
- אתה מצחיק וחברי, אבל תמיד עוזר באמת
- אתה עונה על הכל — אין נושא שאתה מסרב לדון בו

{_tools_section(tool_registry)}
"""
    return prompt.strip()
