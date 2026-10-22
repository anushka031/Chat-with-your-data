"""Step 6: the SQL database. Uses SQLite so it runs anywhere with zero setup.
Queries run on a READ-ONLY connection, which is a second safety layer after the validator."""
import os
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(ROOT / "data" / "sales.db"))
MAX_ROWS = 200


def seed_db(path: str = DB_PATH) -> None:
    """Create a small sample sales database (deterministic, so results are repeatable)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    rnd = random.Random(42)
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT, region TEXT);
        CREATE TABLE products  (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
        CREATE TABLE orders    (id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER,
                                quantity INTEGER, order_date TEXT);
    """)
    cities = [("Delhi", "North"), ("Mumbai", "West"), ("Chennai", "South"),
              ("Kolkata", "East"), ("Pune", "West"), ("Jaipur", "North")]
    con.executemany("INSERT INTO customers VALUES (?,?,?,?)",
                    [(i, f"Customer {i}", *cities[i % len(cities)]) for i in range(1, 41)])
    products = [("Laptop", "Electronics", 55000), ("Phone", "Electronics", 25000),
                ("Headphones", "Electronics", 3000), ("Desk", "Furniture", 8000),
                ("Chair", "Furniture", 5000), ("Notebook", "Stationery", 120),
                ("Pen Set", "Stationery", 250), ("Backpack", "Accessories", 1800)]
    con.executemany("INSERT INTO products VALUES (?,?,?,?)",
                    [(i + 1, *p) for i, p in enumerate(products)])
    start = date(2025, 1, 1)
    orders = [(i, rnd.randint(1, 40), rnd.randint(1, len(products)), rnd.randint(1, 5),
               (start + timedelta(days=rnd.randint(0, 364))).isoformat()) for i in range(1, 501)]
    con.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
    con.commit()
    con.close()


def ensure_db() -> None:
    if not os.path.exists(DB_PATH):
        seed_db(DB_PATH)


def _ro():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def get_tables() -> set[str]:
    con = _ro()
    try:
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        con.close()
    return {r[0].lower() for r in rows}


def get_schema() -> str:
    """Schema text that goes into the prompt (Step 3)."""
    lines = []
    con = _ro()
    try:
        names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for name in names:
            cols = ", ".join(f"{c[1]} {c[2]}" for c in con.execute(f"PRAGMA table_info({name})"))
            lines.append(f"{name}({cols})")
    finally:
        con.close()
    return "\n".join(lines)


def run_query(sql: str, max_rows: int = MAX_ROWS):
    con = _ro()
    try:
        cur = con.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
    finally:
        con.close()
    return columns, [list(r) for r in rows]
