"""Step 2: the backend API (FastAPI). Receives the question and runs the pipeline."""
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.db import ensure_db, get_schema, get_tables, run_query
from backend.formatter import format_result
from backend.llm import generate_sql, mode
from backend.validator import UnsafeSQL, validate_sql

MAX_ATTEMPTS = 3  # the retry loop between the validator (step 5) and the AI (step 4)

app = FastAPI(title="Chat with Your Data")
ensure_db()


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok", "mode": mode()}


@app.get("/schema")
def schema():
    return {"schema": get_schema()}


@app.post("/ask")
def ask(body: Ask):
    schema_text, tables = get_schema(), get_tables()
    last_sql, error = None, None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = generate_sql(body.question, schema_text, last_sql, error)      # step 4
        except Exception as e:
            raise HTTPException(502, f"The AI service failed: {e}")
        try:
            sql = validate_sql(raw, tables)                                      # step 5
            columns, rows = run_query(sql)                                       # step 6
            break
        except UnsafeSQL as e:
            last_sql, error = raw, str(e)
        except sqlite3.Error as e:
            last_sql, error = raw, f"Database error: {e}"
    else:
        raise HTTPException(422, f"Could not produce a safe, working query. Last problem: {error}")

    result = format_result(columns, rows)                                        # step 7
    return {"question": body.question, "sql": sql, "columns": columns, "rows": rows,
            "attempts": attempt, **result}
