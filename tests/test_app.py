import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)  # force DEMO mode so tests never call a real API

import pytest
from fastapi.testclient import TestClient

from backend.db import get_tables
from backend.formatter import format_result
from backend.main import app
from backend.prompt import clean_sql
from backend.validator import UnsafeSQL, validate_sql

client = TestClient(app)
TABLES = get_tables()


def test_validator_allows_select():
    assert validate_sql("SELECT * FROM orders;", TABLES) == "SELECT * FROM orders"


def test_validator_allows_cte_and_join():
    validate_sql("WITH t AS (SELECT * FROM orders) SELECT * FROM t JOIN products p ON p.id = t.product_id", TABLES)


@pytest.mark.parametrize("bad", [
    "DROP TABLE orders",
    "DELETE FROM orders",
    "UPDATE orders SET quantity = 0",
    "INSERT INTO orders VALUES (1,1,1,1,'x')",
    "SELECT 1; DROP TABLE orders",
    "SELECT * FROM secrets",
    "PRAGMA table_info(orders)",
    "",
])
def test_validator_blocks_unsafe(bad):
    with pytest.raises(UnsafeSQL):
        validate_sql(bad, TABLES)


def test_clean_sql_strips_fences():
    assert clean_sql("```sql\nSELECT 1\n```") == "SELECT 1"


def test_formatter_chart_choice():
    assert format_result(["month", "revenue"], [["2025-01", 1], ["2025-02", 2]])["chart"]["type"] == "line"
    assert format_result(["category", "revenue"], [["A", 1], ["B", 2]])["chart"]["type"] == "bar"
    assert format_result(["n"], [[5]])["summary"] == "n: 5"
    assert "No rows" in format_result(["a"], [])["summary"]


def test_ask_end_to_end():
    r = client.post("/ask", json={"question": "revenue by month"})
    assert r.status_code == 200
    body = r.json()
    assert body["sql"].upper().startswith("SELECT")
    assert len(body["rows"]) == 12
    assert body["chart"]["type"] == "line"


def test_ask_rejects_short_question():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_readonly_connection_blocks_writes():
    from backend.db import run_query
    import sqlite3
    with pytest.raises(sqlite3.Error):
        run_query("DELETE FROM orders")
