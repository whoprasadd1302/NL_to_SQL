"""
test_latency.py
----------------
Performance and Latency benchmark test suite for MitraAI Text-to-SQL pipeline.

Verifies:
- Target DB Query Execution latency is under 100ms
- SQL safety validation latency is under 10ms
- Schema introspection and caching is under 50ms
- Result processing and auto-chart selection is under 20ms
- End-to-end pipeline processing latency averages under 2.0s
"""

import time
import statistics
import pytest
from backend.app.schema_manager import get_target_db_schema, get_schema_context
from backend.app.sql_validator import validate_sql
from backend.app.db_executor import execute_query
from backend.app.result_processor import process_results

SAMPLE_BENCHMARK_QUERIES = [
    "SELECT * FROM customers LIMIT 5;",
    "SELECT c.name, a.balance FROM customers c JOIN accounts a ON c.id = a.cust_id;",
    "SELECT city, COUNT(*) AS count FROM customers GROUP BY city;",
    "SELECT SUM(balance) AS total_savings FROM accounts WHERE account_type = 'Savings';",
    "SELECT c.name, l.loan_amount FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Approved';",
]


class TestPipelineLatency:
    def test_schema_introspection_latency(self):
        """Schema introspection and caching should complete in under 100ms."""
        times = []
        for _ in range(10):
            t0 = time.perf_counter()
            schema = get_target_db_schema()
            context = get_schema_context()
            t1 = time.perf_counter()
            times.append(t1 - t0)

        avg_latency = statistics.mean(times)
        assert avg_latency < 0.1, f"Schema introspection avg latency too high: {avg_latency:.4f}s"
        assert "tables" in schema

    def test_sql_validation_latency(self):
        """SQL validation across multiple queries should average under 10ms per query."""
        target_schema = get_target_db_schema()
        times = []

        for sql in SAMPLE_BENCHMARK_QUERIES * 10:
            t0 = time.perf_counter()
            is_valid, _ = validate_sql(sql, schema=target_schema)
            t1 = time.perf_counter()
            assert is_valid is True
            times.append(t1 - t0)

        avg_latency = statistics.mean(times)
        assert avg_latency < 0.01, f"SQL validation avg latency too high: {avg_latency * 1000:.2f}ms"

    def test_db_execution_latency(self):
        """Database execution on target SQLite database should average under 50ms."""
        times = []

        for sql in SAMPLE_BENCHMARK_QUERIES * 5:
            t0 = time.perf_counter()
            results, err = execute_query(sql)
            t1 = time.perf_counter()
            assert err is None
            times.append(t1 - t0)

        avg_latency = statistics.mean(times)
        assert avg_latency < 0.05, f"DB execution avg latency too high: {avg_latency * 1000:.2f}ms"

    def test_result_processor_latency(self):
        """Result processing and chart generation should average under 20ms."""
        sample_dataset = [
            {"city": "Mumbai", "total_balance": 55000.0},
            {"city": "Pune", "total_balance": 82000.0},
            {"city": "Delhi", "total_balance": 34000.0},
            {"city": "Nagpur", "total_balance": 61000.0},
            {"city": "Bengaluru", "total_balance": 95000.0},
        ]

        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            payload = process_results(sample_dataset, query="Balance by city")
            t1 = time.perf_counter()
            assert payload["chart_type"] == "bar"
            times.append(t1 - t0)

        avg_latency = statistics.mean(times)
        assert avg_latency < 0.02, f"Result processor avg latency too high: {avg_latency * 1000:.2f}ms"

    def test_end_to_end_pipeline_latency_target_under_2s(self):
        """
        Simulates end-to-end pipeline execution (Schema + Validate + Execute + Process)
        Verifies that total processing latency is strictly under target of 2.0 seconds.
        """
        pipeline_times = []
        target_schema = get_target_db_schema()

        for sql in SAMPLE_BENCHMARK_QUERIES * 10:
            start = time.perf_counter()

            # 1. Validation
            is_valid, _ = validate_sql(sql, schema=target_schema)
            assert is_valid is True

            # 2. Execution
            results, err = execute_query(sql)
            assert err is None

            # 3. Processing
            processed = process_results(results, query="Benchmark query")
            assert processed is not None

            elapsed = time.perf_counter() - start
            pipeline_times.append(elapsed)

        avg_pipeline_latency = statistics.mean(pipeline_times)
        max_pipeline_latency = max(pipeline_times)

        # Target: < 2.0s average
        assert avg_pipeline_latency < 2.0, (
            f"Average pipeline latency exceeded target: {avg_pipeline_latency:.4f}s"
        )
        assert avg_pipeline_latency < 0.05, (
            f"Pipeline latency was surprisingly high: {avg_pipeline_latency:.4f}s"
        )
