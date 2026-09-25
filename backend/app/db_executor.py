"""
db_executor.py
--------------
SQL Execution Engine for MitraAI Text-to-SQL pipeline.

Executes validated SQL queries against the target database in a secure,
read-only mode with strict execution timeouts.

Features:
- Read-only connection enforcement (SQLite mode=ro + PRAGMA query_only=ON)
- Query timeout enforcement (default 10 seconds)
- Returns results as list[dict] with serialized types
- Connection health check via test_connection()
"""

import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("mitraai.db_executor")

# Default timeout in seconds for query execution
DEFAULT_QUERY_TIMEOUT = 10

# Default target database path
DEFAULT_TARGET_DB_PATH = os.getenv(
    "TARGET_DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "banking.db"))
)


def _resolve_readonly_url(db_path: Optional[str] = None) -> Tuple[str, bool]:
    """
    Resolves the database path to a read-only SQLAlchemy connection URL.

    Returns:
        (db_url: str, is_sqlite: bool)
    """
    if db_path is None or not db_path.strip():
        target = DEFAULT_TARGET_DB_PATH
    else:
        target = db_path.strip()

    # If full URL already provided (e.g. postgresql://, mysql://)
    if "://" in target:
        is_sqlite = target.startswith("sqlite")
        return target, is_sqlite

    abs_path = os.path.abspath(target)
    # Ensure directory exists
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    # SQLite read-only URI
    url = f"sqlite:///file:{abs_path}?mode=ro&uri=true"
    return url, True


def create_readonly_engine(db_path: Optional[str] = None, timeout: int = DEFAULT_QUERY_TIMEOUT) -> Engine:
    """
    Creates a dedicated read-only SQLAlchemy engine for target DB execution.
    """
    db_url, is_sqlite = _resolve_readonly_url(db_path)

    if is_sqlite:
        engine = create_engine(
            db_url,
            connect_args={
                "check_same_thread": False,
                "timeout": timeout,
            },
            pool_pre_ping=True,
        )

        @event.listens_for(engine, "connect")
        def _set_sqlite_read_only(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA query_only = ON;")
                cursor.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)};")
            finally:
                cursor.close()

        return engine

    return create_engine(
        db_url,
        pool_pre_ping=True,
        execution_options={"timeout": timeout},
    )


def test_connection(db_path: Optional[str] = None, timeout: int = DEFAULT_QUERY_TIMEOUT) -> bool:
    """
    Tests if the target database is reachable and can execute queries.

    Args:
        db_path: Target database file path or SQLAlchemy URL. Defaults to banking.db.
        timeout: Connection and query timeout in seconds.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        # Check if local file exists before attempting if it's a file path
        if db_path and "://" not in db_path:
            abs_path = os.path.abspath(db_path)
            if not os.path.exists(abs_path):
                logger.warning(f"Database file does not exist: {abs_path}")
                return False

        engine = create_readonly_engine(db_path, timeout=timeout)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return True
    except Exception as e:
        logger.warning(f"Connection test failed for '{db_path}': {e}")
        return False


def _serialize_value(val: Any) -> Any:
    """Safely converts non-JSON-native database types into JSON-friendly formats."""
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    # Handle dates, times, decimals, bytes
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.hex()
    return str(val)


def execute_query(
    sql: str,
    db_path: Optional[str] = None,
    timeout: int = DEFAULT_QUERY_TIMEOUT,
    max_rows: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Executes a SQL query against the target database in read-only mode.

    Args:
        sql: The SQL SELECT statement to execute.
        db_path: Target database file path or SQLAlchemy URL (defaults to banking.db).
        timeout: Query timeout in seconds (default: 10s).
        max_rows: Optional limit on the number of returned rows.

    Returns:
        Tuple of (results: list[dict], error: Optional[str])
        - On success: (list_of_row_dicts, None)
        - On error:   ([], error_message_str)
    """
    if not sql or not sql.strip():
        return [], "Empty SQL query provided."

    clean_sql = sql.strip().rstrip(";")

    try:
        engine = create_readonly_engine(db_path, timeout=timeout)
        with engine.connect() as conn:
            cursor_result = conn.execute(text(clean_sql))

            # If the query produced no result set (e.g., non-SELECT)
            if not cursor_result.returns_rows:
                return [], None

            # Fetch rows and convert mapping to dict
            rows: List[Dict[str, Any]] = []
            fetched = cursor_result.fetchmany(max_rows) if max_rows else cursor_result.fetchall()

            for row in fetched:
                row_mapping = row._mapping
                row_dict = {col: _serialize_value(row_mapping[col]) for col in row_mapping.keys()}
                rows.append(row_dict)

            return rows, None

    except SQLAlchemyError as e:
        err_msg = str(e.orig) if hasattr(e, "orig") and e.orig else str(e)
        logger.error(f"SQL execution error: {err_msg}")
        return [], f"Database execution error: {err_msg}"
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        return [], f"Execution failed: {str(e)}"
