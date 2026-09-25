"""
test_sql_validator.py
---------------------
Unit tests for backend/app/sql_validator.py

Covers:
- validate_sql happy-path  (valid SELECT queries)
- validate_sql rejection   (DROP, DELETE, UPDATE, ALTER, CREATE, TRUNCATE, INSERT)
- validate_sql table check (unknown table → rejected)
- 10+ injection patterns   (all must be rejected)
- extract_tables           (FROM / JOIN extraction)
- check_injection          (direct injection scanner)
- structural checks        (balanced parens, unclosed strings, multiple statements)
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when pytest is invoked from any CWD
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from backend.app.sql_validator import (
    validate_sql,
    extract_tables,
    check_injection,
    FORBIDDEN_TYPES,
)

# ---------------------------------------------------------------------------
# Shared test schema (mirrors banking.db)
# ---------------------------------------------------------------------------

BANKING_SCHEMA = {
    "tables": ["customers", "accounts", "transactions", "loans"],
    "columns": {
        "customers": [
            {"name": "id",      "type": "INT"},
            {"name": "name",    "type": "TEXT"},
            {"name": "city",    "type": "TEXT"},
            {"name": "balance", "type": "REAL"},
        ],
        "accounts": [
            {"name": "id",           "type": "INT"},
            {"name": "cust_id",      "type": "INT"},
            {"name": "account_type", "type": "TEXT"},
            {"name": "balance",      "type": "REAL"},
        ],
        "transactions": [
            {"name": "id",               "type": "INT"},
            {"name": "account_id",       "type": "INT"},
            {"name": "amount",           "type": "REAL"},
            {"name": "transaction_type", "type": "TEXT"},
            {"name": "transaction_date", "type": "TEXT"},
        ],
        "loans": [
            {"name": "id",          "type": "INT"},
            {"name": "cust_id",     "type": "INT"},
            {"name": "loan_amount", "type": "REAL"},
            {"name": "loan_type",   "type": "TEXT"},
            {"name": "status",      "type": "TEXT"},
        ],
    },
    "foreign_keys": [
        {"from_table": "accounts",     "from_column": "cust_id",    "to_table": "customers", "to_column": "id"},
        {"from_table": "transactions", "from_column": "account_id", "to_table": "accounts",  "to_column": "id"},
        {"from_table": "loans",        "from_column": "cust_id",    "to_table": "customers", "to_column": "id"},
    ],
}


# ===========================================================================
# validate_sql — Happy-path tests
# ===========================================================================

class TestValidateSqlHappyPath:

    def test_simple_select_all(self):
        """SELECT * FROM customers passes all checks."""
        ok, msg = validate_sql("SELECT * FROM customers", BANKING_SCHEMA)
        assert ok is True
        assert msg == "Valid"

    def test_select_with_where(self):
        ok, msg = validate_sql(
            "SELECT * FROM customers WHERE city = 'Mumbai'", BANKING_SCHEMA
        )
        assert ok is True, msg

    def test_select_with_aggregate(self):
        ok, msg = validate_sql(
            "SELECT SUM(balance) AS total FROM accounts WHERE account_type = 'Savings'",
            BANKING_SCHEMA,
        )
        assert ok is True, msg

    def test_select_join(self):
        ok, msg = validate_sql(
            "SELECT c.name, l.loan_amount FROM customers c JOIN loans l ON c.id = l.cust_id",
            BANKING_SCHEMA,
        )
        assert ok is True, msg

    def test_select_without_schema(self):
        """validate_sql skips table-existence check when schema=None."""
        ok, msg = validate_sql("SELECT * FROM unknown_table_xyz", schema=None)
        assert ok is True, msg

    def test_select_lowercase(self):
        ok, msg = validate_sql("select * from customers", BANKING_SCHEMA)
        assert ok is True, msg

    def test_select_with_order_by_and_limit(self):
        ok, msg = validate_sql(
            "SELECT name, balance FROM customers ORDER BY balance DESC LIMIT 5",
            BANKING_SCHEMA,
        )
        assert ok is True, msg

    def test_select_subquery(self):
        ok, msg = validate_sql(
            "SELECT * FROM customers WHERE id IN (SELECT cust_id FROM loans WHERE status = 'Approved')",
            BANKING_SCHEMA,
        )
        assert ok is True, msg

    def test_select_multiple_joins(self):
        ok, msg = validate_sql(
            (
                "SELECT c.name, a.account_type, t.amount "
                "FROM customers c "
                "JOIN accounts a ON c.id = a.cust_id "
                "JOIN transactions t ON a.id = t.account_id"
            ),
            BANKING_SCHEMA,
        )
        assert ok is True, msg


# ===========================================================================
# validate_sql — Forbidden statement rejection
# ===========================================================================

class TestValidateSqlForbiddenStatements:

    def test_drop_table_is_rejected(self):
        """DROP TABLE must be rejected with 'Forbidden' in the error."""
        ok, msg = validate_sql("DROP TABLE customers", BANKING_SCHEMA)
        assert ok is False
        assert "Forbidden" in msg or "DROP" in msg

    def test_delete_is_rejected(self):
        ok, msg = validate_sql("DELETE FROM customers WHERE id = 1", BANKING_SCHEMA)
        assert ok is False
        assert "Forbidden" in msg or "DELETE" in msg

    def test_update_is_rejected(self):
        ok, msg = validate_sql(
            "UPDATE customers SET balance = 0 WHERE id = 1", BANKING_SCHEMA
        )
        assert ok is False
        assert "Forbidden" in msg or "UPDATE" in msg

    def test_alter_is_rejected(self):
        ok, msg = validate_sql("ALTER TABLE customers ADD COLUMN email TEXT", BANKING_SCHEMA)
        assert ok is False
        assert "Forbidden" in msg or "ALTER" in msg

    def test_create_is_rejected(self):
        ok, msg = validate_sql(
            "CREATE TABLE evil (id INT)", BANKING_SCHEMA
        )
        assert ok is False
        assert "Forbidden" in msg or "CREATE" in msg

    def test_truncate_is_rejected(self):
        ok, msg = validate_sql("TRUNCATE TABLE customers", BANKING_SCHEMA)
        assert ok is False
        assert "Forbidden" in msg or "TRUNCATE" in msg

    def test_insert_is_rejected(self):
        ok, msg = validate_sql(
            "INSERT INTO customers (name, city) VALUES ('Eve', 'Delhi')", BANKING_SCHEMA
        )
        assert ok is False
        assert "Forbidden" in msg or "INSERT" in msg

    def test_forbidden_types_constant_completeness(self):
        """All 7 forbidden keywords are present in FORBIDDEN_TYPES constant."""
        expected = {"DROP", "DELETE", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "INSERT"}
        assert expected.issubset(FORBIDDEN_TYPES)


# ===========================================================================
# validate_sql — Table existence check
# ===========================================================================

class TestValidateSqlTableCheck:

    def test_unknown_table_is_rejected(self):
        """Querying a table not in schema returns False."""
        ok, msg = validate_sql("SELECT * FROM unknown_table", BANKING_SCHEMA)
        assert ok is False
        assert "Table not found" in msg or "unknown_table" in msg

    def test_valid_table_passes(self):
        ok, msg = validate_sql("SELECT * FROM loans", BANKING_SCHEMA)
        assert ok is True, msg

    def test_partial_known_join_unknown(self):
        """JOIN referencing unknown table should fail."""
        ok, msg = validate_sql(
            "SELECT * FROM customers JOIN hacker_table ON customers.id = hacker_table.id",
            BANKING_SCHEMA,
        )
        assert ok is False
        assert "hacker_table" in msg or "Table not found" in msg

    def test_all_four_tables_valid(self):
        for table in ["customers", "accounts", "transactions", "loans"]:
            ok, msg = validate_sql(f"SELECT * FROM {table}", BANKING_SCHEMA)
            assert ok is True, f"Expected {table} to be valid, got: {msg}"


# ===========================================================================
# validate_sql — Injection pattern detection (10+ patterns)
# ===========================================================================

class TestInjectionPatternRejection:
    """
    Each entry is (description, sql_string).
    ALL must be rejected by validate_sql.
    """

    INJECTION_CASES = [
        ("OR 1=1 tautology",
         "SELECT * FROM customers WHERE 1=1 OR 1=1"),

        ("SQL line comment (--)",
         "SELECT * FROM customers -- injected comment"),

        ("Stacked DROP statement",
         "SELECT * FROM customers; DROP TABLE customers;"),

        ("UNION SELECT extraction",
         "SELECT * FROM customers UNION SELECT * FROM accounts"),

        ("String tautology (OR '1'='1')",
         "SELECT * FROM customers WHERE name = '' OR '1'='1'"),

        ("SLEEP time-based blind injection",
         "SELECT SLEEP(5) FROM customers"),

        ("WAITFOR DELAY time-based injection",
         "SELECT * FROM customers WHERE id = 1 WAITFOR DELAY '0:0:5'"),

        ("System schema access (sys.)",
         "SELECT * FROM sys.tables"),

        ("information_schema access",
         "SELECT * FROM information_schema.tables"),

        ("xp_cmdshell OS execution",
         "EXEC xp_cmdshell('whoami')"),

        ("Block comment obfuscation",
         "SELECT * FROM customers /* injected */"),

        ("BENCHMARK time-based injection",
         "SELECT BENCHMARK(1000000, SHA1('test')) FROM customers"),

        ("Hex-encoded payload",
         "SELECT * FROM customers WHERE name = 0x61646D696E"),

        ("CHAR() encoding",
         "SELECT * FROM customers WHERE name = CHAR(65,66,67)"),
    ]

    @pytest.mark.parametrize("description,sql", INJECTION_CASES)
    def test_injection_is_rejected(self, description: str, sql: str):
        ok, msg = validate_sql(sql, BANKING_SCHEMA)
        assert ok is False, (
            f"Expected injection to be rejected [{description}] but got ok=True, msg={msg!r}"
        )


# ===========================================================================
# check_injection — Direct unit tests
# ===========================================================================

class TestCheckInjection:

    def test_clean_sql_not_flagged(self):
        is_injected, label = check_injection("SELECT * FROM customers WHERE city = 'Mumbai'")
        assert is_injected is False
        assert label == ""

    def test_or_1_equals_1(self):
        is_injected, label = check_injection("SELECT * FROM t WHERE 1=1 OR 1=1")
        assert is_injected is True
        assert "1=1" in label or "Tautology" in label

    def test_union_select(self):
        is_injected, label = check_injection("SELECT id FROM t UNION SELECT id FROM u")
        assert is_injected is True
        assert "UNION" in label

    def test_comment_injection(self):
        is_injected, label = check_injection("SELECT * FROM t -- drop tables")
        assert is_injected is True
        assert "comment" in label.lower() or "--" in label

    def test_sleep_injection(self):
        is_injected, label = check_injection("SELECT SLEEP(5)")
        assert is_injected is True

    def test_system_schema(self):
        is_injected, label = check_injection("SELECT * FROM information_schema.tables")
        assert is_injected is True

    def test_into_outfile(self):
        is_injected, label = check_injection("SELECT * FROM t INTO OUTFILE '/tmp/evil'")
        assert is_injected is True


# ===========================================================================
# extract_tables — Unit tests
# ===========================================================================

class TestExtractTables:

    def test_single_table_from(self):
        assert extract_tables("SELECT * FROM customers") == ["customers"]

    def test_join_two_tables(self):
        tables = extract_tables(
            "SELECT c.name FROM customers c JOIN accounts a ON c.id = a.cust_id"
        )
        assert "customers" in tables
        assert "accounts" in tables

    def test_three_table_join(self):
        tables = extract_tables(
            "SELECT c.name, a.account_type, t.amount "
            "FROM customers c "
            "JOIN accounts a ON c.id = a.cust_id "
            "JOIN transactions t ON a.id = t.account_id"
        )
        assert "customers" in tables
        assert "accounts" in tables
        assert "transactions" in tables

    def test_returns_lowercase(self):
        tables = extract_tables("SELECT * FROM Customers")
        assert tables == ["customers"]

    def test_deduplication(self):
        tables = extract_tables("SELECT * FROM customers")
        assert len(tables) == len(set(tables))

    def test_no_table_in_select_1(self):
        tables = extract_tables("SELECT 1")
        assert tables == []


# ===========================================================================
# Structural checks
# ===========================================================================

class TestStructuralChecks:

    def test_unbalanced_parenthesis_rejected(self):
        ok, msg = validate_sql("SELECT * FROM customers WHERE (id = 1", BANKING_SCHEMA)
        assert ok is False
        assert "Unbalanced" in msg or "paren" in msg.lower()

    def test_extra_closing_paren_rejected(self):
        ok, msg = validate_sql("SELECT * FROM customers WHERE id = 1)", BANKING_SCHEMA)
        assert ok is False

    def test_balanced_parenthesis_passes(self):
        ok, msg = validate_sql(
            "SELECT * FROM customers WHERE (city = 'Mumbai')", BANKING_SCHEMA
        )
        assert ok is True, msg

    def test_empty_sql_rejected(self):
        ok, msg = validate_sql("", BANKING_SCHEMA)
        assert ok is False
        assert "empty" in msg.lower()

    def test_whitespace_only_rejected(self):
        ok, msg = validate_sql("   \n\t  ", BANKING_SCHEMA)
        assert ok is False

    def test_multiple_statements_rejected(self):
        ok, msg = validate_sql(
            "SELECT * FROM customers; SELECT * FROM loans", BANKING_SCHEMA
        )
        assert ok is False
        assert "Multiple" in msg or "multiple" in msg
