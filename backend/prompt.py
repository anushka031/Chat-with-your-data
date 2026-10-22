"""Step 3: the prompt builder. Adds the database structure so the AI knows what exists."""
import re

SYSTEM = (
    "You convert questions into a single SQLite SELECT query.\n"
    "Rules: use only the tables and columns given; write read-only SELECT queries only; "
    "return ONLY the SQL, with no explanation and no markdown."
)


def build_prompt(question: str, schema: str, last_sql: str | None = None, error: str | None = None) -> str:
    text = f"Database schema:\n{schema}\n\nQuestion: {question}\n"
    if last_sql and error:
        text += f"\nYour previous query was:\n{last_sql}\nIt failed with: {error}\nFix it and return only the corrected SQL.\n"
    return text


def clean_sql(text: str) -> str:
    """Remove ```sql fences if the model added them anyway."""
    text = text.strip()
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    return (match.group(1) if match else text).strip()
