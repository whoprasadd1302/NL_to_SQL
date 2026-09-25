import os
import sys
from pathlib import Path

# Ensure project root is in sys.path when running pytest directly
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from backend.app.schema_manager import (
    get_target_db_schema,
    get_schema_context,
    get_table_names,
    get_column_names,
    clear_cache,
)


def test_get_target_db_schema_returns_4_tables():
    """Test: get_target_db_schema returns 4 tables and full schema dictionary."""
    clear_cache()
    schema = get_target_db_schema()

    assert isinstance(schema, dict)
    assert "tables" in schema
    assert "columns" in schema
    assert "foreign_keys" in schema

    # Verify 4 tables returned
    assert len(schema["tables"]) == 4
    expected_tables = ["customers", "accounts", "transactions", "loans"]
    for table in expected_tables:
        assert table in schema["tables"]
        assert table in schema["columns"]

    # Verify column structures
    customer_cols = [c["name"] for c in schema["columns"]["customers"]]
    assert customer_cols == ["id", "name", "city", "balance"]

    account_cols = [c["name"] for c in schema["columns"]["accounts"]]
    assert "cust_id" in account_cols
    assert "account_type" in account_cols

    # Verify foreign keys
    assert len(schema["foreign_keys"]) >= 3
    fk_relationships = [fk["relationship"] for fk in schema["foreign_keys"]]
    assert "accounts.cust_id → customers.id" in fk_relationships


def test_get_schema_context_returns_formatted_string():
    """Test: get_schema_context returns formatted string for LLM prompting."""
    clear_cache()
    context = get_schema_context("")

    assert isinstance(context, str)
    assert "Tables:" in context
    assert "- customers: id (INT), name (TEXT), city (TEXT), balance (REAL)" in context
    assert "- accounts: id (INT), cust_id (INT), account_type (TEXT), balance (REAL)" in context
    assert "Foreign Keys:" in context
    assert "- accounts.cust_id → customers.id" in context


def test_get_table_names_returns_expected_list():
    """Test: get_table_names returns ['customers', 'accounts', 'transactions', 'loans']."""
    clear_cache()
    tables = get_table_names()
    assert tables == ["customers", "accounts", "transactions", "loans"]


def test_get_column_names():
    """Test: get_column_names returns list of columns for specified table."""
    clear_cache()
    assert get_column_names("customers") == ["id", "name", "city", "balance"]
    assert get_column_names("accounts") == ["id", "cust_id", "account_type", "balance"]
    assert get_column_names("transactions") == [
        "id",
        "account_id",
        "amount",
        "transaction_type",
        "transaction_date",
    ]
    assert get_column_names("loans") == [
        "id",
        "cust_id",
        "loan_amount",
        "loan_type",
        "status",
    ]


def test_clear_cache():
    """Test: clear_cache correctly invalidates in-memory cache."""
    clear_cache()
    schema1 = get_target_db_schema()
    assert schema1 is not None

    clear_cache()
    from backend.app.schema_manager import _SCHEMA_CACHE

    assert len(_SCHEMA_CACHE) == 0

    schema2 = get_target_db_schema()
    assert len(_SCHEMA_CACHE) == 1
    assert schema2["tables"] == schema1["tables"]
