"""
sql_validator.py
----------------
SQL Safety Validator for MitraAI Text-to-SQL pipeline.

Performs a layered defence-in-depth validation before any SQL reaches the
execution engine:

  Layer 1 – Empty / parse guard
  Layer 2 – Injection pattern detection  (regex, applied FIRST)
  Layer 3 – Forbidden statement rejection (DROP / DELETE / UPDATE / …)
  Layer 4 – SELECT-only enforcement      (first token must be SELECT DML)
  Layer 5 – Table existence check        (tables extracted vs schema)
  Layer 6 – Structural integrity check  (balanced parentheses / quotes)
  Layer 7 – Multiple-statement guard     (only a single statement allowed)
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple

import sqlparse
import sqlparse.tokens as T

logger = logging.getLogger("mitraai.sql_validator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# SQL statement types that are completely forbidden in a read-only pipeline
FORBIDDEN_TYPES: frozenset = frozenset({
    "DROP",
    "DELETE",
    "UPDATE",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "INSERT",
})

# Injection detection patterns: (compiled_regex, human-readable label)
# Applied in order; first match short-circuits.
_RAW_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    # Classic tautologies
    (r"\bOR\s+1\s*=\s*1\b",               "Tautology: OR 1=1"),
    (r"\bAND\s+1\s*=\s*1\b",              "Tautology: AND 1=1"),
    (r"\bOR\s+'[^']*'\s*=\s*'[^']*'",    "Tautology: OR string=string"),
    (r"\bAND\s+'[^']*'\s*=\s*'[^']*'",   "Tautology: AND string=string"),
    # Comment injections
    (r"--",                                "SQL comment (--)"),
    (r"/\*.*?\*/",                         "Block comment (/* */)"),
    (r"#",                                 "MySQL comment (#)"),
    # Stacked / chained statements
    (r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC)\b",
     "Multiple statements (stacked query)"),
    # UNION-based extraction
    (r"\bUNION\s+(ALL\s+)?SELECT\b",      "UNION SELECT injection"),
    # Time-based blind injection
    (r"\bSLEEP\s*\(",                     "Time-based: SLEEP()"),
    (r"\bWAITFOR\s+DELAY\b",             "Time-based: WAITFOR DELAY"),
    (r"\bBENCHMARK\s*\(",                "Time-based: BENCHMARK()"),
    (r"\bPG_SLEEP\s*\(",                  "Time-based: PG_SLEEP()"),
    # System / metadata table access
    (r"\b(sys|information_schema|mysql|pg_catalog|pg_)\.",
     "System schema access"),
    # OS / shell execution
    (r"\b(xp_cmdshell|xp_exec|sp_execute|sp_executesql)\b",
     "OS command execution"),
    (r"\bEXEC\s*\(",                      "EXEC() call"),
    # Encoding obfuscation
    (r"\bCHAR\s*\(\s*\d+",              "CHAR() encoding"),
    (r"0x[0-9a-fA-F]+",                  "Hex encoding"),
    # Dangerous functions
    (r"\bLOAD_FILE\s*\(",               "LOAD_FILE()"),
    (r"\bINTO\s+OUTFILE\b",             "INTO OUTFILE"),
    (r"\bINTO\s+DUMPFILE\b",            "INTO DUMPFILE"),
]

# Pre-compile for speed
INJECTION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(raw, re.IGNORECASE | re.DOTALL), label)
    for raw, label in _RAW_INJECTION_PATTERNS
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _first_meaningful_token(parsed: sqlparse.sql.Statement) -> Optional[sqlparse.sql.Token]:
    """Returns the first non-whitespace token from a parsed statement."""
    for token in parsed.flatten():
        if not token.is_whitespace:
            return token
    return None


def _check_balanced(sql: str) -> bool:
    """
    Returns True when parentheses are balanced and string literals are closed.
    Ignores quoted characters inside string literals.
    """
    depth: int = 0
    in_string: bool = False
    string_char: str = ""

    for ch in sql:
        if in_string:
            if ch == string_char:
                in_string = False
        else:
            if ch in ("'", '"', "`"):
                in_string = True
                string_char = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    return False

    return depth == 0 and not in_string


# ---------------------------------------------------------------------------
# Core public functions
# ---------------------------------------------------------------------------

def check_injection(sql: str) -> Tuple[bool, str]:
    """
    Scans the SQL string for known injection signatures.

    Args:
        sql: Raw SQL string (may still contain markdown or extra whitespace).

    Returns:
        (is_injected, pattern_label)
        - is_injected: True if a suspicious pattern is detected.
        - pattern_label: Human-readable name of the matched pattern, or "".
    """
    for pattern, label in INJECTION_PATTERNS:
        if pattern.search(sql):
            logger.warning("Injection pattern detected: %s | SQL: %.80s", label, sql)
            return True, label
    return False, ""


def extract_tables(sql: str) -> List[str]:
    """
    Extracts table names referenced in FROM / JOIN clauses using sqlparse.

    Handles:
    - Simple FROM <table>
    - Table aliases:  FROM <table> <alias>
    - Multiple JOINs: JOIN <table> ON ...
    - Sub-selects are NOT recursed into (surface-level only)

    Returns:
        Deduplicated list of lowercased table names in order of appearance.
    """
    try:
        parsed = sqlparse.parse(sql.strip())[0]
    except Exception:
        return []

    tables: List[str] = []
    from_seen: bool = False

    join_keywords = frozenset({
        "FROM", "JOIN", "INNER", "LEFT", "RIGHT", "CROSS", "FULL", "OUTER",
    })
    skip_ttypes = frozenset({
        T.Whitespace,
        T.Text.Whitespace,
        T.Text.Whitespace.Newline,
        T.Newline,
        T.Punctuation,
    })

    for token in parsed.flatten():
        normalized = token.normalized.upper()

        if token.ttype is T.Keyword and normalized in join_keywords:
            from_seen = True
            continue

        if from_seen:
            if token.ttype is T.Name:
                table_name = token.value.strip().strip("`").strip('"')
                if table_name:
                    tables.append(table_name.lower())
                from_seen = False
            elif token.ttype in skip_ttypes or normalized == "JOIN":
                # Skip whitespace / punctuation, keep looking
                continue
            else:
                from_seen = False

    # Preserve first-seen order, deduplicate
    seen: Dict[str, int] = {}
    for t in tables:
        if t not in seen:
            seen[t] = 1
    return list(seen.keys())


def validate_sql(
    sql: str,
    schema: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Validates a SQL string through all defence layers.

    Args:
        sql:    The SQL string to validate (may be dirty — extraction strips later).
        schema: Optional schema dict from schema_manager.get_target_db_schema().
                When provided, tables referenced in the query are verified against
                the known table list.  Pass None to skip the table check.

    Returns:
        (is_valid, message)
        - is_valid: True only if ALL checks pass.
        - message:  "Valid" on success, or a descriptive error string.

    Checks (in order):
        1. Empty / whitespace guard
        2. Injection pattern detection
        3. Multiple-statement guard
        4. Forbidden statement type (DROP / DELETE / UPDATE / …)
        5. SELECT-only enforcement (first DML token must be SELECT)
        6. Table existence in schema
        7. Balanced parentheses / string literals
    """
    # ── 1. Empty guard ───────────────────────────────────────────────────────
    cleaned = sql.strip()
    if not cleaned:
        return False, "SQL is empty"

    # ── 2. Injection detection ────────────────────────────────────────────────
    is_injected, pattern_label = check_injection(cleaned)
    if is_injected:
        return False, f"Injection detected: {pattern_label}"

    # ── 3. Multiple-statement guard ───────────────────────────────────────────
    #    sqlparse.parse() returns one Statement per ";" separator.
    try:
        statements = [
            s for s in sqlparse.parse(cleaned) if s.get_type() is not None
        ]
    except Exception as exc:
        return False, f"Parse error: {exc}"

    if len(statements) > 1:
        return False, "Multiple SQL statements are not allowed"

    if not statements:
        # Could not parse any recognisable statement
        return False, "Could not parse SQL statement"

    stmt = statements[0]
    stmt_type: Optional[str] = stmt.get_type()

    # ── 4. Forbidden statement type ───────────────────────────────────────────
    if stmt_type and stmt_type.upper() in FORBIDDEN_TYPES:
        return False, f"Forbidden statement type: {stmt_type.upper()}"

    # ── 5. First token must be SELECT ─────────────────────────────────────────
    first_token = _first_meaningful_token(stmt)
    if first_token is None:
        return False, "SQL contains no meaningful tokens"

    first_val = first_token.normalized.upper()

    # Catch forbidden keywords even when sqlparse misclassifies type
    if first_val in FORBIDDEN_TYPES:
        return False, f"Forbidden: {first_val}"

    if first_token.ttype is not T.Keyword.DML or first_val != "SELECT":
        return False, f"Only SELECT statements are permitted (got: {first_val!r})"

    # ── 6. Table existence check ──────────────────────────────────────────────
    if schema is not None:
        known_tables: List[str] = [t.lower() for t in schema.get("tables", [])]
        referenced_tables = extract_tables(cleaned)
        for table in referenced_tables:
            if table not in known_tables:
                return False, f"Table not found in schema: '{table}'"

    # ── 7. Structural integrity ───────────────────────────────────────────────
    if not _check_balanced(cleaned):
        return False, "Unbalanced parentheses or unclosed string literal"

    return True, "Valid"
