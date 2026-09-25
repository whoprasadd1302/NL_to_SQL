"""
test_db_executor.py
-------------------
Unit tests for backend/app/db_executor.py

Covers:
- execute_query happy path (SELECT * FROM customers LIMIT 5)
- execute_query invalid SQL returns empty results and error message
- execute_query on custom sqlite db path fixture
- execute_query readonly enforcement (write queries fail)
- execute_query empty/whitespace query handling
- execute_query with limits/max_rows
- test_connection returns True for valid database
- test_connection returns False for non-existent database file
"""

import os
import pytest
import sqlite3
from sqlalchemy import create_engine, text
from backend.app.db_executor import (
    execute_query,
    test_connection as db_test_connection,
    create_readonly_engine,
    _resolve_readonly_url,
    DEFAULT_TARGET_DB_PATH,
)


@pytest.fixture
def temp_test_db(tmp_path):
    """Creates a temporary SQLite database with test schema and data."""
    db_file = str(tmp_path / "test_target.db")
    engine = create_engine(f"sqlite:///{db_file}")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT,
                balance REAL
            );
        """))
        conn.execute(text("""
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                cust_id INTEGER,
                balance REAL
            );
        """))
        conn.execute(text("""
            INSERT INTO customers (id, name, city, balance) VALUES
            (1, 'Alice', 'Mumbai', 50000.0),
            (2, 'Bob', 'Pune', 75000.0),
            (3, 'Charlie', 'Delhi', 30000.0),
            (4, 'David', 'Nagpur', 45000.0),
            (5, 'Eve', 'Bengaluru', 90000.0),
            (6, 'Frank', 'Chennai', 60000.0);
        """))
        conn.execute(text("""
            INSERT INTO accounts (id, cust_id, balance) VALUES
            (101, 1, 50000.0),
            (102, 2, 75000.0);
        """))
    return db_file


# ---------------------------------------------------------------------------
# Test execute_query
# ---------------------------------------------------------------------------

class TestExecuteQuery:
    def test_execute_query_limit_5_records(self, temp_test_db):
        """execute_query('SELECT * FROM customers LIMIT 5') returns exactly 5 records."""
        results, error = execute_query("SELECT * FROM customers LIMIT 5", db_path=temp_test_db)
        assert error is None
        assert isinstance(results, list)
        assert len(results) == 5
        assert results[0]["id"] == 1
        assert results[0]["name"] == "Alice"
        assert results[0]["city"] == "Mumbai"
        assert results[0]["balance"] == 50000.0
        assert results[4]["name"] == "Eve"

    def test_execute_query_on_default_banking_db(self):
        """execute_query on default banking.db returns records without error."""
        results, error = execute_query("SELECT * FROM customers LIMIT 5")
        assert error is None
        assert isinstance(results, list)
        assert len(results) >= 1
        assert "name" in results[0]
        assert "city" in results[0]

    def test_execute_query_invalid_sql(self, temp_test_db):
        """execute_query('INVALID SQL') returns empty list and error message."""
        results, error = execute_query("INVALID SQL SYNTAX HERE", db_path=temp_test_db)
        assert results == []
        assert error is not None
        assert isinstance(error, str)
        assert len(error) > 0

    def test_execute_query_non_existent_table(self, temp_test_db):
        """execute_query on non-existent table returns error."""
        results, error = execute_query("SELECT * FROM non_existent_table_xyz", db_path=temp_test_db)
        assert results == []
        assert error is not None
        assert "no such table" in error.lower() or "error" in error.lower()

    def test_execute_query_empty_sql(self, temp_test_db):
        """Empty or whitespace-only SQL returns error."""
        results, error = execute_query("", db_path=temp_test_db)
        assert results == []
        assert error is not None
        assert "empty" in error.lower()

        results, error = execute_query("   ", db_path=temp_test_db)
        assert results == []
        assert error is not None

    def test_execute_query_with_join(self, temp_test_db):
        """execute_query handles JOIN queries properly."""
        sql = """
            SELECT c.name, a.balance 
            FROM customers c 
            JOIN accounts a ON c.id = a.cust_id 
            ORDER BY c.id
        """
        results, error = execute_query(sql, db_path=temp_test_db)
        assert error is None
        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[0]["balance"] == 50000.0

    def test_execute_query_readonly_enforcement(self, temp_test_db):
        """Writing (INSERT / UPDATE / DROP) must fail due to readonly connection."""
        # Attempting INSERT
        results, error = execute_query(
            "INSERT INTO customers (id, name, city, balance) VALUES (99, 'Hacker', 'Nowhere', 0)",
            db_path=temp_test_db
        )
        assert results == []
        assert error is not None
        assert "readonly" in error.lower() or "read-only" in error.lower() or "attempt to write" in error.lower()

    def test_execute_query_max_rows_limit(self, temp_test_db):
        """max_rows parameter truncates row count safely."""
        results, error = execute_query("SELECT * FROM customers", db_path=temp_test_db, max_rows=2)
        assert error is None
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Test test_connection
# ---------------------------------------------------------------------------

class TestTestConnection:
    def test_test_connection_default_db(self):
        """test_connection() returns True for default banking DB."""
        assert db_test_connection() is True

    def test_test_connection_valid_custom_db(self, temp_test_db):
        """test_connection() returns True for existing custom DB."""
        assert db_test_connection(temp_test_db) is True

    def test_test_connection_non_existent_file(self, tmp_path):
        """test_connection() returns False for non-existent database file."""
        non_existent = str(tmp_path / "does_not_exist" / "missing.db")
        assert db_test_connection(non_existent) is False


# ---------------------------------------------------------------------------
# Test create_readonly_engine & URL resolution
# ---------------------------------------------------------------------------

class TestEngineConfig:
    def test_resolve_readonly_url_default(self):
        """Resolving without args points to DEFAULT_TARGET_DB_PATH with mode=ro."""
        url, is_sqlite = _resolve_readonly_url()
        assert is_sqlite is True
        assert "mode=ro" in url
        assert "uri=true" in url

    def test_create_readonly_engine_returns_engine(self, temp_test_db):
        """create_readonly_engine returns functional SQLAlchemy Engine."""
        engine = create_readonly_engine(temp_test_db)
        with engine.connect() as conn:
            val = conn.execute(text("SELECT 42")).scalar()
            assert val == 42
