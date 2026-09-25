"""
test_endpoints.py
-----------------
Unit and integration tests for FastAPI NL-to-SQL endpoints in backend/app/main.py.

Covers:
- GET /sql/schema returns target database schema JSON
- POST /sql/execute returns generated SQL, executed results, summary, and chart metadata
- POST /sql/stream streams Server-Sent Events with SQL tokens
- POST /sql/export generates downloadable CSV content
- Error handling on invalid/empty requests
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test GET /sql/schema
# ---------------------------------------------------------------------------

def test_get_sql_schema():
    """GET /sql/schema returns tables, columns, foreign keys, and context."""
    response = client.get("/sql/schema")
    assert response.status_code == 200
    data = response.json()

    assert "tables" in data
    assert "columns" in data
    assert "foreign_keys" in data
    assert "schema_context" in data

    assert isinstance(data["tables"], list)
    assert "customers" in data["tables"]
    assert "accounts" in data["tables"]
    assert "transactions" in data["tables"]
    assert "loans" in data["tables"]
    assert "Tables:" in data["schema_context"]


# ---------------------------------------------------------------------------
# Test POST /sql/execute
# ---------------------------------------------------------------------------

@patch("backend.app.main.generate_sql")
def test_execute_sql_success(mock_generate_sql):
    """POST /sql/execute generates SQL, executes it, and returns results payload."""
    mock_generate_sql.return_value = "SELECT * FROM customers WHERE city = 'Mumbai';"

    payload = {
        "query": "Mumbai ke customers dikhao",
        "language": "hi",
        "session_id": "test-session-123",
    }
    response = client.post("/sql/execute", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["language"] == "hi"
    assert data["language_name"] == "Hindi"
    assert data["sql"] == "SELECT * FROM customers WHERE city = 'Mumbai';"
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1
    assert "summary" in data
    assert "chart_type" in data
    assert "chart_data" in data
    assert "execution_time" in data
    assert data["count"] == len(data["results"])


def test_execute_sql_empty_query():
    """POST /sql/execute with empty query returns 400."""
    response = client.post("/sql/execute", json={"query": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@patch("backend.app.main.generate_sql")
def test_execute_sql_validation_failure(mock_generate_sql):
    """POST /sql/execute returns success=False when generated SQL fails validation."""
    mock_generate_sql.return_value = "DROP TABLE customers;"

    payload = {"query": "Delete all customers"}
    response = client.post("/sql/execute", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is False
    assert data["sql"] == "DROP TABLE customers;"
    assert "validation failed" in data["error"].lower()
    assert data["results"] == []


# ---------------------------------------------------------------------------
# Test POST /sql/stream
# ---------------------------------------------------------------------------

@patch("backend.app.main.generate_sql_stream")
def test_stream_sql_success(mock_generate_stream):
    """POST /sql/stream streams SSE tokens and finishes with done=True payload."""
    mock_generate_stream.return_value = ["SELECT ", "* ", "FROM ", "customers;"]

    payload = {
        "query": "Show all customers",
        "language": "auto",
    }
    response = client.post("/sql/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    content = response.text
    assert "data: {\"token\": \"SELECT \"}" in content
    assert "data: {\"done\": true, \"sql\": \"SELECT * FROM customers;\"}" in content


def test_stream_sql_empty_query():
    """POST /sql/stream with empty query returns 400."""
    response = client.post("/sql/stream", json={"query": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Test POST /sql/export
# ---------------------------------------------------------------------------

def test_export_sql_results_with_provided_data():
    """POST /sql/export converts provided list of dicts to CSV attachment."""
    payload = {
        "data": [
            {"id": 1, "name": "Alice", "balance": 50000.0},
            {"id": 2, "name": "Bob", "balance": 75000.0},
        ]
    }
    response = client.post("/sql/export", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=query_results.csv" in response.headers["content-disposition"]

    csv_text = response.text
    assert "id,name,balance" in csv_text
    assert "Alice" in csv_text
    assert "Bob" in csv_text


def test_export_sql_results_with_sql():
    """POST /sql/export executes SQL query and returns CSV attachment."""
    payload = {
        "sql": "SELECT * FROM customers LIMIT 2;"
    }
    response = client.post("/sql/export", json=payload)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    csv_text = response.text
    assert "name" in csv_text
    assert "city" in csv_text
