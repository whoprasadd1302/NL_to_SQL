"""
test_security.py
----------------
Security and SQL Injection Prevention test suite for MitraAI.

Tests 10+ distinct SQL injection vectors and malicious inputs:
1. Classic tautology (OR 1=1)
2. String tautology (OR 'a'='a')
3. Line comment injection (--)
4. Block comment obfuscation (/* ... */)
5. Stacked query execution (; DROP TABLE)
6. Stacked update statement (; UPDATE accounts)
7. UNION SELECT data exfiltration
8. Time-based blind injection (SLEEP)
9. Time-based blind injection (WAITFOR DELAY)
10. System catalog / metadata table access (information_schema / sys)
11. OS command execution (xp_cmdshell / EXEC)
12. Out-of-band file dump (INTO OUTFILE)
13. Hex / Char encoded payloads

Verifies that:
- check_injection() flags every payload as injected
- validate_sql() strictly rejects every payload (is_valid == False)
- db_executor() fails safely in read-only mode if any write is attempted
"""

import pytest
from backend.app.sql_validator import validate_sql, check_injection
from backend.app.schema_manager import get_target_db_schema
from backend.app.db_executor import execute_query

INJECTION_VECTORS = [
    # (Label, Malicious SQL payload)
    ("Tautology numeric OR 1=1", "SELECT * FROM customers WHERE id = 1 OR 1=1;"),
    ("Tautology numeric AND 1=1", "SELECT * FROM accounts WHERE 1=1 AND 1=1;"),
    ("Tautology string OR 'x'='x'", "SELECT * FROM customers WHERE name = '' OR 'admin'='admin';"),
    ("Line comment bypass (--)", "SELECT * FROM customers WHERE id = 1 -- ignore rest of query;"),
    ("Block comment obfuscation (/* */)", "SELECT * FROM customers WHERE id = 1 /* bypass */ AND balance > 0;"),
    ("Stacked DROP TABLE statement", "SELECT * FROM customers; DROP TABLE customers;"),
    ("Stacked UPDATE statement", "SELECT * FROM accounts; UPDATE accounts SET balance = 1000000;"),
    ("Stacked DELETE statement", "SELECT * FROM transactions; DELETE FROM transactions;"),
    ("UNION SELECT exfiltration", "SELECT name, city FROM customers UNION SELECT cust_id, balance FROM accounts;"),
    ("Time-based blind injection (SLEEP)", "SELECT * FROM customers WHERE id = 1 AND SLEEP(5);"),
    ("Time-based blind injection (WAITFOR DELAY)", "SELECT * FROM customers WHERE id = 1 WAITFOR DELAY '0:0:5';"),
    ("Time-based blind injection (BENCHMARK)", "SELECT * FROM customers WHERE id = 1 AND BENCHMARK(1000000, MD5(1));"),
    ("System schema access (sys.tables)", "SELECT * FROM sys.tables;"),
    ("Metadata access (information_schema)", "SELECT * FROM information_schema.tables;"),
    ("OS command execution (xp_cmdshell)", "EXEC xp_cmdshell('dir C:\\');"),
    ("Direct EXEC invocation", "EXEC('SELECT * FROM customers');"),
    ("File exfiltration (INTO OUTFILE)", "SELECT * FROM customers INTO OUTFILE '/tmp/dump.txt';"),
    ("File read (LOAD_FILE)", "SELECT LOAD_FILE('/etc/passwd');"),
    ("Hex encoded payload", "SELECT * FROM customers WHERE name = 0x61646D696E;"),
    ("CHAR() encoded payload", "SELECT * FROM customers WHERE name = CHAR(97,100,109,105,110);"),
]


class TestSecurityAndInjectionDefense:
    @pytest.mark.parametrize("label, payload", INJECTION_VECTORS)
    def test_check_injection_flags_all_malicious_vectors(self, label, payload):
        """Verify check_injection identifies each injection vector."""
        is_injected, matched_pattern = check_injection(payload)
        assert is_injected is True, f"Failed to detect injection for: {label} ({payload})"
        assert len(matched_pattern) > 0

    @pytest.mark.parametrize("label, payload", INJECTION_VECTORS)
    def test_validate_sql_rejects_all_malicious_vectors(self, label, payload):
        """Verify validate_sql returns is_valid=False for every malicious vector."""
        target_schema = get_target_db_schema()
        is_valid, msg = validate_sql(payload, schema=target_schema)
        assert is_valid is False, f"validate_sql unexpectedly allowed: {label} ({payload})"
        assert msg != "Valid"

    @pytest.mark.parametrize("write_sql", [
        "INSERT INTO customers (id, name, city, balance) VALUES (99, 'Hacker', 'Nowhere', 0);",
        "UPDATE customers SET balance = 999999 WHERE id = 1;",
        "DELETE FROM customers WHERE id = 1;",
        "DROP TABLE IF EXISTS customers;",
    ])
    def test_db_executor_readonly_mode_blocks_writes(self, write_sql):
        """Verify db_executor readonly connection enforces SQLite query_only mode."""
        results, err = execute_query(write_sql)
        assert results == []
        assert err is not None
        assert any(kw in err.lower() for kw in ["readonly", "read-only", "attempt to write", "error"])
