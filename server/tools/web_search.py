import httpx
import os

def search_web(query: str, num_results: int = 5) -> str:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    if not api_key or not cx:
        return "כלי החיפוש לא מוגדר."

    r = httpx.get(
        "https://www.googleapis.com/customsearch/v1",
        params={"key": api_key, "cx": cx, "q": query, "num": int(num_results)},
        timeout=10,
    )
    data = r.json()
    items = data.get("items", [])
    if not items:
        return f"לא נמצאו תוצאות עבור: {query}"

    lines = []
    for item in items:
        lines.append(f"- **{item.get('title')}**\n  {item.get('snippet', '')}\n  {item.get('link')}")
    return "\n\n".join(lines)


from tools import TOOL_REGISTRY

TOOL_REGISTRY["search_web"] = {
    "schema": {
        "name": "search_web",
        "description": "מחפש מידע באינטרנט — מזג אוויר, חדשות, עובדות, כל דבר",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "מה לחפש"},
                "num_results": {"type": "integer", "description": "כמה תוצאות להחזיר (ברירת מחדל 5)"},
            },
            "required": ["query"],
        },
    },
    "fn": search_web,
}
