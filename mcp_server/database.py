# mcp_server/database.py
import os
import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from .audit_logger import log_sql
import time
import inspect
from datetime import datetime

# Load .env file
load_dotenv()

_FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
    "merge",
    "call",
)


def _ensure_read_only(sql: str) -> None:
    """Ensure the provided SQL statement is read-only (SELECT/CTE)."""
    if not sql or not isinstance(sql, str):
        raise ValueError("SQL must be a non-empty string.")

    # Strip line and block comments
    sanitized = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.DOTALL)
    stripped = sanitized.strip()

    if not stripped:
        raise ValueError("SQL cannot be empty after removing comments.")

    # Disallow multiple statements separated by semicolons (except optional trailing)
    trailing_stripped = stripped.rstrip("; \n\t\r")
    if ";" in trailing_stripped:
        raise ValueError("Only single read-only statements are permitted.")

    # Accept statements that start with SELECT or WITH clauses (allow wrapping parens)
    leading = stripped.lstrip("(").lstrip()
    heading = leading[:5].lower()
    if not (leading.lower().startswith("select") or leading.lower().startswith("with")):
        raise ValueError("Only SELECT/CTE read queries are allowed.")

    lowered = stripped.lower()
    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise ValueError(f"Keyword '{keyword}' is not permitted in read-only mode.")

    return stripped


class Database:
    def __init__(self):
        """Create connection when Database() is initialized"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DATABASE_HOST"),
                port=int(os.getenv("DATABASE_PORT")),
                database=os.getenv("DATABASE_NAME"),
                user=os.getenv("DATABASE_USER"),
                password=os.getenv("DATABASE_PASSWORD")
            )
            print(" Connected to PostgreSQL!")
        except Exception as e:
            print(f"Connection failed: {e}")
            raise
    def execute_query(self, sql: str, params=None) -> dict:
        """
        Execute a SQL query and return results.
        Logs the statement, params, caller, and duration.
        """
        

        try:
            # Ensure read-only & get sanitized SQL
            sanitized_sql = _ensure_read_only(sql)

            # Who called me (e.g., get_pr_summary)
            caller_fn = None
            try:
                caller_fn = inspect.stack()[1].function
            except Exception:
                caller_fn = "unknown_caller"

            # Normalize params just for consistent logging (psycopg2 accepts None or seq)
            # inside execute_query before log_params
            if params is None:
                log_params = ()
            elif isinstance(params, (list, tuple)):
                log_params = tuple(params)
            else:
                log_params = (params,)

            # ---- Logging: start ----
            start = time.time()
            print("\n" + "=" * 80, file=sys.stderr, flush=True)
            print(f"[DB] {datetime.now():%Y-%m-%d %H:%M:%S} | caller: {caller_fn}", file=sys.stderr, flush=True)
            print("[DB] SQL:", sanitized_sql.strip(), file=sys.stderr, flush=True)
            if log_params:
                print("[DB] Params:", log_params, file=sys.stderr, flush=True)
            log_sql(sanitized_sql.strip())
            # ---- Logging: start ----

            cursor = self.conn.cursor(cursor_factory=RealDictCursor)

            # Execute the **sanitized** SQL (not the original)
            if params is not None:
                cursor.execute(sanitized_sql, params)
                try:
                    interpolated = cursor.mogrify(sanitized_sql, params).decode()
                    log_sql(interpolated)
                except Exception:
                    pass
            else:
                cursor.execute(sanitized_sql)
                log_sql(sanitized_sql)

            rows = cursor.fetchall()
            cursor.close()

            elapsed_ms = (time.time() - start) * 1000.0
            print(f"[DB] OK: {len(rows)} rows in {elapsed_ms:.2f} ms", file=sys.stderr, flush=True)
            print("=" * 80 + "\n", file=sys.stderr, flush=True)

            return {
                "success": True,
                "rows": [dict(row) for row in rows],
                "count": len(rows),
            }

        except Exception as e:
            # Log the error too
            print(f"[DB] ERROR: {e}", file=sys.stderr, flush=True)
            print("=" * 80 + "\n", file=sys.stderr, flush=True)
            return {"success": False, "error": str(e)}

    def close(self):
        """Close the database connection"""
        self.conn.close()
        print(" Database connection closed")
    
