"""
result_processor.py
-------------------
Query Result Processing and Visualization Module for MitraAI.

Processes raw database query results into structured payloads for frontend consumption,
including automatic natural language summary generation and chart type selection.

Features:
- Result dataset normalization with pandas DataFrame
- Automatic chart type selection ("number_card", "bar", "line", "table", None)
- Chart dataset preparation suitable for Chart.js / Recharts
- Natural language summary generation
"""

import sys
import logging
from typing import Any, Dict, List, Optional, Union
import pandas as pd

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("mitraai.result_processor")


def select_chart_type(df: pd.DataFrame) -> Optional[str]:
    """
    Automatically selects an appropriate visualization chart type based on DataFrame structure.

    Rules:
    - Empty DataFrame -> None
    - Single number (1 row x 1 numeric column) -> "number_card"
    - 1 numeric column + 1 categorical column -> "bar"
    - 2 numeric columns -> "line"
    - Other multi-row results -> "table"

    Args:
        df: Input pandas DataFrame.

    Returns:
        Chart type string ("number_card", "bar", "line", "table") or None.
    """
    if df is None or df.empty:
        return None

    num_rows, num_cols = df.shape

    # Single number check (1 row, 1 column, numeric)
    if num_rows == 1 and num_cols == 1:
        col = df.columns[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            return "number_card"

    # Identify numeric and non-numeric (categorical/string/date) columns
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols]

    num_numeric = len(numeric_cols)
    num_non_numeric = len(non_numeric_cols)

    # 1 numeric + 1 categorical -> "bar"
    if num_cols == 2 and num_numeric == 1 and num_non_numeric == 1:
        return "bar"

    # 2 numeric columns -> "line"
    if num_cols == 2 and num_numeric == 2:
        return "line"

    # Fallback rules for 1 numeric + 1 categorical or 2 numeric in multi-column scenarios
    if num_numeric == 1 and num_non_numeric == 1:
        return "bar"
    if num_numeric == 2 and num_non_numeric == 0:
        return "line"

    return "table"


def prepare_chart_data(df: pd.DataFrame, chart_type: Optional[str]) -> Dict[str, Any]:
    """
    Formats the DataFrame into structured chart payload for the frontend.

    Args:
        df: Input pandas DataFrame.
        chart_type: Target chart type string ("number_card", "bar", "line", "table").

    Returns:
        Dictionary formatted for visualization components.
    """
    if df is None or df.empty or not chart_type:
        return {}

    if chart_type == "number_card":
        col = df.columns[0]
        val = df.iloc[0, 0]
        formatted_val = float(val) if isinstance(val, (int, float)) and not pd.isna(val) else val
        return {
            "type": "number_card",
            "title": str(col),
            "value": formatted_val
        }

    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols]

    if chart_type == "bar":
        label_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
        value_col = numeric_cols[0] if numeric_cols else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
        labels = [str(x) for x in df[label_col].tolist()]
        values = [float(x) if pd.notnull(x) else 0.0 for x in df[value_col].tolist()]
        return {
            "type": "bar",
            "x_axis": str(label_col),
            "y_axis": str(value_col),
            "labels": labels,
            "series": [{"name": str(value_col), "data": values}]
        }

    if chart_type == "line":
        col1 = df.columns[0]
        col2 = df.columns[1] if len(df.columns) > 1 else col1
        x_vals = [str(x) for x in df[col1].tolist()]
        y_vals = [float(x) if pd.notnull(x) else 0.0 for x in df[col2].tolist()]
        return {
            "type": "line",
            "x_axis": str(col1),
            "y_axis": str(col2),
            "labels": x_vals,
            "series": [{"name": str(col2), "data": y_vals}]
        }

    return {
        "type": "table",
        "columns": [str(c) for c in df.columns],
        "rows": df.to_dict(orient="records")
    }


def generate_summary(df: pd.DataFrame, query: Optional[str] = None) -> str:
    """
    Generates a natural language summary of query results.

    Args:
        df: Input pandas DataFrame.
        query: Optional user natural language query string.

    Returns:
        Natural language string describing the result dataset.
    """
    if df is None or df.empty:
        return "No results found for your query."

    num_rows, num_cols = df.shape

    if num_rows == 1 and num_cols == 1:
        val = df.iloc[0, 0]
        col_name = df.columns[0]
        return f"The total {col_name.replace('_', ' ')} is {val}."

    if num_rows == 1:
        details = ", ".join([f"{col}: {val}" for col, val in df.iloc[0].items()])
        return f"Found 1 record with details: {details}."

    columns_str = ", ".join([str(c) for c in df.columns])
    return f"Retrieved {num_rows} records containing: {columns_str}."


def process_results(
    data: Union[List[Dict[str, Any]], pd.DataFrame],
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes raw query execution data into a complete payload for the frontend UI.

    Args:
        data: List of dicts or pandas DataFrame representing raw database results.
        query: Optional user natural language query.

    Returns:
        Dict containing summary, chart_type, chart_data, row_count, columns, and data list.
    """
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame()

    chart_type = select_chart_type(df)
    summary = generate_summary(df, query)
    chart_data = prepare_chart_data(df, chart_type)

    records = df.to_dict(orient="records") if not df.empty else []
    columns = [str(c) for c in df.columns] if not df.empty else []

    return {
        "summary": summary,
        "chart_type": chart_type,
        "chart_data": chart_data,
        "data": records,
        "row_count": len(records),
        "columns": columns,
    }
