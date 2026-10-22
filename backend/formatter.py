"""Step 7: the result formatter. Picks a simple summary and a sensible chart type."""
import re


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def format_result(columns: list[str], rows: list[list]) -> dict:
    if not rows:
        return {"summary": "No rows matched your question.", "chart": None}
    if len(rows) == 1 and len(columns) == 1:
        return {"summary": f"{columns[0]}: {rows[0][0]}", "chart": None}

    summary = f"Returned {len(rows)} row{'s' if len(rows) != 1 else ''}."
    chart = None
    if len(columns) == 2 and 2 <= len(rows) <= 30 and all(_is_number(r[1]) for r in rows):
        looks_like_time = bool(re.search(r"date|month|year|week|day", columns[0], re.I)) or \
            all(re.match(r"^\d{4}(-\d{2})?", str(r[0])) for r in rows)
        chart = {"type": "line" if looks_like_time else "bar", "x": columns[0], "y": columns[1]}
    return {"summary": summary, "chart": chart}
