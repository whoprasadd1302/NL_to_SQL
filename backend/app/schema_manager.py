import os
import sys
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("mitraai.schema_manager")

# In-memory schema cache: cache_key -> dict(tables, columns, foreign_keys)
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

# Default target database path
DEFAULT_TARGET_DB_PATH = os.getenv(
    "TARGET_DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "banking.db"))
)

PREFERRED_TABLE_ORDER = ["customers", "accounts", "transactions", "loans"]


def _format_column_type(col_type: Any) -> str:
    """Normalizes SQL column types to standard prompt representations (e.g. INT, TEXT, REAL)."""
    raw_type = str(col_type).upper().strip()
    if raw_type.startswith("INTEGER") or raw_type == "INT":
        return "INT"
    if (
        raw_type.startswith("VARCHAR")
        or raw_type.startswith("CHAR")
        or raw_type.startswith("STRING")
        or raw_type.startswith("TEXT")
    ):
        return "TEXT"
    if (
        raw_type.startswith("REAL")
        or raw_type.startswith("FLOAT")
        or raw_type.startswith("DOUBLE")
        or raw_type.startswith("NUMERIC")
        or raw_type.startswith("DECIMAL")
    ):
        return "REAL"
    return raw_type.replace("()", "")


def _initialize_sample_banking_db(file_path: str) -> None:
    """Creates a sample banking SQLite database with the standard 4 tables if not already present."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    engine = create_engine(f"sqlite:///{os.path.abspath(file_path)}")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT,
                balance REAL DEFAULT 0.0
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                cust_id INTEGER NOT NULL,
                account_type TEXT,
                balance REAL DEFAULT 0.0,
                FOREIGN KEY (cust_id) REFERENCES customers (id)
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                account_id INTEGER NOT NULL,
                amount REAL,
                transaction_type TEXT,
                transaction_date TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY,
                cust_id INTEGER NOT NULL,
                loan_amount REAL,
                loan_type TEXT,
                status TEXT,
                FOREIGN KEY (cust_id) REFERENCES customers (id)
            );
        """))

        # Seed data if empty
        count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if not count:
            conn.execute(text("""
                INSERT INTO customers (id, name, city, balance) VALUES
                (1, 'Ramesh Sharma', 'Mumbai', 55000.0),
                (2, 'Priya Patel', 'Pune', 82000.0),
                (3, 'Amit Verma', 'Delhi', 34000.0),
                (4, 'Sneha Kulkarni', 'Nagpur', 61000.0);
            """))
            conn.execute(text("""
                INSERT INTO accounts (id, cust_id, account_type, balance) VALUES
                (101, 1, 'Savings', 55000.0),
                (102, 2, 'Current', 82000.0),
                (103, 3, 'Savings', 34000.0),
                (104, 4, 'Savings', 61000.0);
            """))
            conn.execute(text("""
                INSERT INTO transactions (id, account_id, amount, transaction_type, transaction_date) VALUES
                (1001, 101, 5000.0, 'Credit', '2026-01-15'),
                (1002, 101, 1200.0, 'Debit', '2026-01-20'),
                (1003, 102, 15000.0, 'Credit', '2026-02-01'),
                (1004, 103, 3000.0, 'Debit', '2026-02-10');
            """))
            conn.execute(text("""
                INSERT INTO loans (id, cust_id, loan_amount, loan_type, status) VALUES
                (501, 1, 500000.0, 'Home', 'Approved'),
                (502, 2, 200000.0, 'Car', 'Active'),
                (503, 3, 100000.0, 'Personal', 'Pending');
            """))
    logger.info(f"Initialized sample banking database at {file_path}")


def _resolve_engine(db_path: Optional[str] = None) -> tuple[str, Engine]:
    """Resolves database path to a cache key and an initialized SQLAlchemy Engine."""
    if db_path is None:
        target_path = DEFAULT_TARGET_DB_PATH
    else:
        target_path = db_path

    if "://" in target_path:
        cache_key = target_path
        engine = create_engine(target_path)
        return cache_key, engine

    abs_path = os.path.abspath(target_path)
    if not os.path.exists(abs_path):
        _initialize_sample_banking_db(abs_path)

    cache_key = abs_path
    engine = create_engine(f"sqlite:///{abs_path}")
    return cache_key, engine


def clear_cache() -> None:
    """Clears the in-memory schema cache."""
    _SCHEMA_CACHE.clear()


def get_target_db_schema(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Introspects the target database schema using SQLAlchemy inspect().
    Caches the schema in memory.

    Returns:
        dict with keys:
            - 'tables': list of table names
            - 'columns': dict of table_name -> list of column dicts
            - 'foreign_keys': list of foreign key relationship dicts
    """
    cache_key, engine = _resolve_engine(db_path)

    if cache_key in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[cache_key]

    inspector = inspect(engine)
    raw_tables = inspector.get_table_names()

    # Sort tables placing known banking tables first, then alphabetically
    tables = sorted(
        raw_tables,
        key=lambda t: (
            PREFERRED_TABLE_ORDER.index(t)
            if t in PREFERRED_TABLE_ORDER
            else 999,
            t,
        ),
    )

    columns: Dict[str, List[Dict[str, Any]]] = {}
    foreign_keys: List[Dict[str, Any]] = []

    for table in tables:
        cols_raw = inspector.get_columns(table)
        cols_formatted = []
        for c in cols_raw:
            cols_formatted.append({
                "name": c["name"],
                "type": _format_column_type(c.get("type", "TEXT")),
                "primary_key": bool(c.get("primary_key", False)),
                "nullable": bool(c.get("nullable", True)),
            })
        columns[table] = cols_formatted

        fks_raw = inspector.get_foreign_keys(table)
        for fk in fks_raw:
            ref_table = fk.get("referred_table")
            constrained_cols = fk.get("constrained_columns", [])
            referred_cols = fk.get("referred_columns", [])
            for c_col, r_col in zip(constrained_cols, referred_cols):
                foreign_keys.append({
                    "from_table": table,
                    "from_column": c_col,
                    "to_table": ref_table,
                    "to_column": r_col,
                    "relationship": f"{table}.{c_col} → {ref_table}.{r_col}",
                })

    schema = {
        "tables": tables,
        "columns": columns,
        "foreign_keys": foreign_keys,
    }

    _SCHEMA_CACHE[cache_key] = schema
    return schema


def get_table_names(db_path: Optional[str] = None) -> List[str]:
    """Returns a list of table names present in the target database."""
    schema = get_target_db_schema(db_path)
    return schema.get("tables", [])


def get_column_names(table: str, db_path: Optional[str] = None) -> List[str]:
    """Returns a list of column names for the specified table."""
    schema = get_target_db_schema(db_path)
    table_cols = schema.get("columns", {}).get(table, [])
    return [c["name"] for c in table_cols]


def get_schema_context(query: str = "", db_path: Optional[str] = None) -> str:
    """
    Formats the introspected database schema for LLM prompting.

    Example output:
    Tables:
    - customers: id (INT), name (TEXT), city (TEXT), balance (REAL)
    - accounts: id (INT), cust_id (INT), account_type (TEXT), balance (REAL)
    - transactions: id (INT), account_id (INT), amount (REAL), transaction_type (TEXT), transaction_date (TEXT)
    - loans: id (INT), cust_id (INT), loan_amount (REAL), loan_type (TEXT), status (TEXT)
    Foreign Keys:
    - accounts.cust_id → customers.id
    - transactions.account_id → accounts.id
    - loans.cust_id → customers.id
    """
    schema = get_target_db_schema(db_path)

    lines: List[str] = ["Tables:"]
    for table in schema.get("tables", []):
        cols = schema.get("columns", {}).get(table, [])
        cols_str = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
        lines.append(f"- {table}: {cols_str}")

    foreign_keys = schema.get("foreign_keys", [])
    if foreign_keys:
        lines.append("Foreign Keys:")
        for fk in foreign_keys:
            lines.append(f"- {fk['from_table']}.{fk['from_column']} → {fk['to_table']}.{fk['to_column']}")

    return "\n".join(lines)
