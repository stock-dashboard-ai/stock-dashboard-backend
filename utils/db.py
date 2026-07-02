import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db() -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS mda (
                        ticker TEXT PRIMARY KEY,
                        filing_date TEXT,
                        summary TEXT,
                        full_text TEXT
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS financials (
                        ticker TEXT PRIMARY KEY,
                        data JSONB
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS embedded (
                        ticker TEXT PRIMARY KEY
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        ticker TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_history_session
                    ON chat_history(session_id)
                """)
    finally:
        conn.close()


def reset_all() -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "TRUNCATE TABLE mda, financials, embedded, chat_history"
                )
    finally:
        conn.close()


def get_mda(ticker: str) -> dict | None:
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT filing_date, summary, full_text FROM mda WHERE ticker = %s",
                (ticker,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def set_mda(
    ticker: str, filing_date: str | None, summary: str | None, full_text: str | None
) -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mda (ticker, filing_date, summary, full_text)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (ticker) DO UPDATE SET
                        filing_date = EXCLUDED.filing_date,
                        summary = EXCLUDED.summary,
                        full_text = EXCLUDED.full_text
                    """,
                    (ticker, filing_date, summary, full_text),
                )
    finally:
        conn.close()


def get_financials(ticker: str) -> dict | None:
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT data FROM financials WHERE ticker = %s", (ticker,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def set_financials(ticker: str, data: dict) -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO financials (ticker, data)
                    VALUES (%s, %s)
                    ON CONFLICT (ticker) DO UPDATE SET data = EXCLUDED.data
                    """,
                    (ticker, Json(data)),
                )
    finally:
        conn.close()


def get_embedded(ticker: str) -> bool:
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM embedded WHERE ticker = %s", (ticker,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def set_embedded(ticker: str) -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO embedded (ticker) VALUES (%s) ON CONFLICT DO NOTHING",
                    (ticker,),
                )
    finally:
        conn.close()


def get_chat_history(session_id: str) -> list[dict]:
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT role, content FROM chat_history WHERE session_id = %s ORDER BY created_at",
                (session_id,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def append_chat_turn(session_id: str, ticker: str, role: str, content: str) -> None:
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (session_id, ticker, role, content) VALUES (%s, %s, %s, %s)",
                    (session_id, ticker, role, content),
                )
    finally:
        conn.close()
