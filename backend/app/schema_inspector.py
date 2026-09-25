import time
import logging
from typing import Dict, List, Any
from sqlalchemy import inspect, text
from .database import engine

logger = logging.getLogger("mitraai")

_schema_cache: Dict[str, Any] = {}
_schema_cache_time: float = 0


def get_database_schema(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Introspects the connected database and returns structured schema information
    including tables, columns, data types, primary keys, and foreign keys.
    Cached in memory for 60 seconds to optimize response speed.
    """
    global _schema_cache, _schema_cache_time
    now = time.time()
    if not force_refresh and _schema_cache and (now - _schema_cache_time < 60):
        return _schema_cache

    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        try:
            view_names = inspector.get_view_names()
            table_names = list(set(table_names + view_names))
        except Exception:
            pass
        
        # Exclude internal MitraAI chat tables if querying dataset
        excluded_tables = {"chat_sessions", "chat_messages"}
        dataset_tables = [t for t in table_names if t not in excluded_tables]
        
        # If only chat tables exist, include all tables
        active_tables = dataset_tables if dataset_tables else table_names

        schema_info: Dict[str, Any] = {}

        for table in active_tables:
            columns = inspector.get_columns(table)
            pk = inspector.get_pk_constraint(table)
            fks = inspector.get_foreign_keys(table)

            schema_info[table] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                    }
                    for col in columns
                ],
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": [
                    {
                        "constrained_columns": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", []),
                    }
                    for fk in fks
                ],
            }

        _schema_cache = schema_info
        _schema_cache_time = now
        return schema_info
    except Exception as e:
        logger.error(f"Error inspecting database schema: {e}")
        return _schema_cache or {}


def format_schema_for_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Formats the introspected schema into a readable SQL schema summary for the LLM prompt.
    """
    if not schema_info:
        return "No external dataset tables detected in the database yet."

    schema_lines = []
    for table, details in schema_info.items():
        cols_desc = ", ".join([f"{col['name']} ({col['type']})" for col in details["columns"]])
        pk_desc = f", PRIMARY KEY ({', '.join(details['primary_key'])})" if details.get("primary_key") else ""
        
        fk_descs = []
        for fk in details.get("foreign_keys", []):
            fk_descs.append(
                f"FOREIGN KEY ({', '.join(fk['constrained_columns'])}) REFERENCES {fk['referred_table']}({', '.join(fk['referred_columns'])})"
            )
        fk_str = (", " + ", ".join(fk_descs)) if fk_descs else ""
        
        schema_lines.append(f"CREATE TABLE {table} (\n  {cols_desc}{pk_desc}{fk_str}\n);")

    return "\n\n".join(schema_lines)


def execute_safe_sql(query: str, max_rows: int = 100) -> Dict[str, Any]:
    """
    Safely executes a read-only SQL SELECT query and returns rows & column headers.
    """
    query_clean = query.strip().rstrip(";")
    
    # Basic safety validation: only allow SELECT queries
    first_word = query_clean.split()[0].upper() if query_clean else ""
    if first_word != "SELECT" and first_word != "WITH":
        return {
            "success": False,
            "error": "Only read-only SELECT or CTE queries are permitted for safety.",
            "columns": [],
            "rows": [],
            "row_count": 0,
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query_clean))
            columns = list(result.keys())
            raw_rows = result.fetchmany(max_rows)
            # Convert row tuples to list of serializable dicts or values
            rows = [list(row) for row in raw_rows]

            # Try to get true total row count with a COUNT(*) wrapper
            total_count = len(rows)
            try:
                count_result = connection.execute(text(f"SELECT COUNT(*) FROM ({query_clean}) AS _count_query"))
                total_count = count_result.scalar() or len(rows)
            except Exception:
                total_count = len(rows)

            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": total_count,
                "fetched_count": len(rows),
                "truncated": len(rows) < total_count,
                "error": None,
            }
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return {
            "success": False,
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0,
        }
