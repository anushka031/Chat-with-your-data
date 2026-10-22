# Chat with Your Data

Ask a question in plain English. The app writes SQL, checks it is safe, runs it, and shows the answer with a table and a chart.

## Run it

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1: backend
uvicorn backend.main:app --reload

# Terminal 2: chat screen
streamlit run frontend/app.py
```

With no API key the app runs in **demo mode** (canned SQL for the sample data) so you can see it work immediately.
For the real AI, set `ANTHROPIC_API_KEY` (see `.env.example`) before starting the backend, for example `export ANTHROPIC_API_KEY=...`.

Run the tests: `python -m pytest`

## How the files match the 8 steps

| Step | What it does | File |
|---|---|---|
| 1, 8 | Chat screen, shows the answer | `frontend/app.py` |
| 2 | Backend API (FastAPI) | `backend/main.py` |
| 3 | Prompt builder (adds table structure) | `backend/prompt.py` |
| 4 | AI writes SQL | `backend/llm.py` |
| 5 | SQL validator (SELECT only) | `backend/validator.py` |
| 6 | SQL database (read-only connection) | `backend/db.py` |
| 7 | Result formatter (summary, chart type) | `backend/formatter.py` |

The retry loop (validator back to the AI, up to 3 tries) is in `backend/main.py`.

## Safety, in two layers
1. The validator allows only one SELECT statement on known tables.
2. The database connection itself is read-only, so even a missed bad query cannot change data.

## Ideas to extend it (good for your resume)
- Swap SQLite for PostgreSQL (change `backend/db.py` only).
- Add your own dataset instead of the sample one.
- Add a small set of test questions with expected answers to measure how often the AI gets it right, and report that number honestly.
- Deploy it (for example Streamlit Community Cloud plus a free backend host) and put the live link on your resume.
