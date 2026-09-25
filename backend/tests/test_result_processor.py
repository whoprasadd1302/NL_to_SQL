"""
test_result_processor.py
------------------------
Unit tests for backend/app/result_processor.py

Covers:
- process_results returns dict with summary, chart_type, data, row_count, columns
- select_chart_type returns "bar" for 1 categorical + 1 numeric
- select_chart_type returns "line" for 2 numeric columns
- select_chart_type returns "number_card" for single number result
- select_chart_type returns None for empty DataFrame
- generate_summary returns expected natural language strings for single row, multi-row, empty results
- prepare_chart_data formats structure correctly for bar, line, number_card, and table
"""

import pytest
import pandas as pd
from backend.app.result_processor import (
    process_results,
    generate_summary,
    select_chart_type,
    prepare_chart_data,
)


class TestSelectChartType:
    def test_select_chart_type_empty(self):
        """Empty DataFrame returns None."""
        df = pd.DataFrame()
        assert select_chart_type(df) is None

        assert select_chart_type(None) is None

    def test_select_chart_type_single_number(self):
        """1 row, 1 numeric column returns 'number_card'."""
        df = pd.DataFrame([{"total_customers": 42}])
        assert select_chart_type(df) == "number_card"

    def test_select_chart_type_bar(self):
        """1 categorical + 1 numeric returns 'bar'."""
        data = [
            {"city": "Mumbai", "customer_count": 120},
            {"city": "Pune", "customer_count": 80},
            {"city": "Delhi", "customer_count": 150},
        ]
        df = pd.DataFrame(data)
        assert select_chart_type(df) == "bar"

    def test_select_chart_type_line(self):
        """2 numeric columns return 'line'."""
        data = [
            {"year": 2021, "total_sales": 50000.0},
            {"year": 2022, "total_sales": 75000.0},
            {"year": 2023, "total_sales": 110000.0},
        ]
        df = pd.DataFrame(data)
        assert select_chart_type(df) == "line"

    def test_select_chart_type_multi_column_table(self):
        """3+ mixed columns default to 'table'."""
        data = [
            {"id": 1, "name": "Alice", "city": "Mumbai", "balance": 50000.0},
            {"id": 2, "name": "Bob", "city": "Pune", "balance": 75000.0},
        ]
        df = pd.DataFrame(data)
        assert select_chart_type(df) == "table"


class TestGenerateSummary:
    def test_generate_summary_empty(self):
        """Empty DataFrame returns no results string."""
        df = pd.DataFrame()
        summary = generate_summary(df, "Show customers")
        assert "No results found" in summary

    def test_generate_summary_single_number(self):
        """Single number result produces descriptive sentence."""
        df = pd.DataFrame([{"count": 150}])
        summary = generate_summary(df, "How many customers?")
        assert "count" in summary
        assert "150" in summary

    def test_generate_summary_single_row(self):
        """Single row result returns 1 record details."""
        df = pd.DataFrame([{"name": "Alice", "city": "Mumbai"}])
        summary = generate_summary(df)
        assert "Found 1 record" in summary
        assert "Alice" in summary

    def test_generate_summary_multi_row(self):
        """Multi-row result returns count and column names."""
        data = [
            {"name": "Alice", "balance": 5000.0},
            {"name": "Bob", "balance": 7000.0},
        ]
        df = pd.DataFrame(data)
        summary = generate_summary(df)
        assert "Retrieved 2 records" in summary
        assert "name" in summary
        assert "balance" in summary


class TestPrepareChartData:
    def test_prepare_chart_data_number_card(self):
        """Formats number card correctly."""
        df = pd.DataFrame([{"total_balance": 250000.50}])
        chart_data = prepare_chart_data(df, "number_card")
        assert chart_data["type"] == "number_card"
        assert chart_data["title"] == "total_balance"
        assert chart_data["value"] == 250000.50

    def test_prepare_chart_data_bar(self):
        """Formats bar chart series and labels correctly."""
        data = [
            {"city": "Mumbai", "users": 10},
            {"city": "Delhi", "users": 20},
        ]
        df = pd.DataFrame(data)
        chart_data = prepare_chart_data(df, "bar")
        assert chart_data["type"] == "bar"
        assert chart_data["labels"] == ["Mumbai", "Delhi"]
        assert chart_data["series"][0]["data"] == [10.0, 20.0]

    def test_prepare_chart_data_line(self):
        """Formats line chart series correctly."""
        data = [
            {"month": 1, "revenue": 1000.0},
            {"month": 2, "revenue": 1500.0},
        ]
        df = pd.DataFrame(data)
        chart_data = prepare_chart_data(df, "line")
        assert chart_data["type"] == "line"
        assert chart_data["labels"] == ["1", "2"]
        assert chart_data["series"][0]["data"] == [1000.0, 1500.0]


class TestProcessResults:
    def test_process_results_returns_dict_with_summary_and_chart_type(self):
        """process_results returns full output payload dict."""
        data = [
            {"city": "Mumbai", "total": 500},
            {"city": "Pune", "total": 300},
        ]
        res = process_results(data, query="Show total by city")
        assert isinstance(res, dict)
        assert "summary" in res
        assert "chart_type" in res
        assert "chart_data" in res
        assert "data" in res
        assert "row_count" in res
        assert "columns" in res

        assert res["chart_type"] == "bar"
        assert res["row_count"] == 2
        assert res["columns"] == ["city", "total"]
        assert len(res["data"]) == 2
        assert "Retrieved 2 records" in res["summary"]

    def test_process_results_with_empty_input(self):
        """process_results handles empty input list cleanly."""
        res = process_results([])
        assert res["chart_type"] is None
        assert res["row_count"] == 0
        assert res["data"] == []
        assert "No results found" in res["summary"]
