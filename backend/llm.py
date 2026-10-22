"""Step 4: the AI writes SQL. Real mode uses the Anthropic API; DEMO mode needs no key."""
import os

from backend.prompt import SYSTEM, build_prompt, clean_sql

REVENUE = "ROUND(SUM(o.quantity * p.price), 2)"


def _demo_sql(question: str) -> str:
    """Canned queries for the sample database so the app runs without an API key."""
    q = question.lower()
    if "month" in q:
        return (f"SELECT strftime('%Y-%m', o.order_date) AS month, {REVENUE} AS revenue "
                "FROM orders o JOIN products p ON p.id = o.product_id GROUP BY month ORDER BY month")
    if "categor" in q:
        return (f"SELECT p.category, {REVENUE} AS revenue FROM orders o "
                "JOIN products p ON p.id = o.product_id GROUP BY p.category ORDER BY revenue DESC")
    if "region" in q:
        return (f"SELECT c.region, {REVENUE} AS revenue FROM orders o "
                "JOIN products p ON p.id = o.product_id JOIN customers c ON c.id = o.customer_id "
                "GROUP BY c.region ORDER BY revenue DESC")
    if "how many" in q and "customer" in q:
        return "SELECT COUNT(*) AS customers FROM customers"
    if "customer" in q:
        return (f"SELECT c.name, {REVENUE} AS total_spent FROM orders o "
                "JOIN products p ON p.id = o.product_id JOIN customers c ON c.id = o.customer_id "
                "GROUP BY c.id ORDER BY total_spent DESC LIMIT 5")
    return (f"SELECT p.name, {REVENUE} AS revenue FROM orders o "
            "JOIN products p ON p.id = o.product_id GROUP BY p.id ORDER BY revenue DESC LIMIT 5")


def mode() -> str:
    return "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "demo"


def generate_sql(question: str, schema: str, last_sql: str | None = None, error: str | None = None) -> str:
    if mode() == "demo":
        return _demo_sql(question)
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=os.getenv("MODEL", "claude-sonnet-4-6"),
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(question, schema, last_sql, error)}],
    )
    return clean_sql(response.content[0].text)
