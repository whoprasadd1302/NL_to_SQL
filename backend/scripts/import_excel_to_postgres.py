"""
Excel to PostgreSQL Importer for MitraAI College Dataset
Reads all sheets from an Excel file (.xlsx) and creates/populates PostgreSQL tables.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from backend/.env
backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)
sys.path.insert(0, str(backend_dir))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from app.config import DATABASE_URL


def clean_identifier(name: str) -> str:
    """Cleans table or column names for SQL compatibility."""
    cleaned = str(name).strip().lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)  # Remove special chars
    cleaned = re.sub(r"\s+", "_", cleaned)     # Replace whitespace with underscore
    if cleaned and cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned or "column"


def import_file(file_path: str, table_override: str = None, if_exists: str = "replace"):
    """
    Imports all sheets from an Excel file (.xlsx, .xls) or a CSV file into PostgreSQL.
    """
    path = Path(file_path)
    if not path.exists():
        print(f"[!] Error: File not found at '{file_path}'")
        return False

    print(f"\n[*] Reading dataset file: {path.name}")
    print(f"    Database target: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    summary = []

    if path.suffix.lower() == ".csv":
        # CSV handling
        table_name = clean_identifier(table_override or path.stem)
        df = pd.read_csv(path)
        df.columns = [clean_identifier(c) for c in df.columns]
        
        if if_exists == "replace":
            with engine.begin() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
        
        df.to_sql(name=table_name, con=engine, if_exists="replace" if if_exists == "replace" else if_exists, index=False)
        summary.append({"sheet": "CSV", "table": table_name, "rows": len(df), "cols": len(df.columns)})
        print(f"    [+] Successfully imported {len(df)} rows and {len(df.columns)} columns into '{table_name}'")
    else:
        # Excel handling
        excel_file = pd.ExcelFile(path)
        sheet_names = excel_file.sheet_names
        print(f"[*] Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}\n")

        for sheet in sheet_names:
            if table_override and len(sheet_names) == 1:
                table_name = clean_identifier(table_override)
            else:
                table_name = clean_identifier(sheet)
                if table_name in ("sheet1", "sheet_1") and "student" in path.name.lower():
                    table_name = "students"

            if not table_name:
                table_name = "college_data"

            print(f"[*] Processing sheet: '{sheet}' -> Table: '{table_name}'...")
            df = pd.read_excel(excel_file, sheet_name=sheet)

            if df.empty:
                print(f"    [!] Sheet '{sheet}' is empty, skipping.")
                continue

            # Clean column names
            df.columns = [clean_identifier(c) for c in df.columns]

            # Handle duplicate column names
            seen = {}
            new_cols = []
            for col in df.columns:
                if col in seen:
                    seen[col] += 1
                    new_cols.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    new_cols.append(col)
            df.columns = new_cols

            # Write to PostgreSQL
            try:
                if if_exists == "replace":
                    with engine.begin() as conn:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
                
                df.to_sql(name=table_name, con=engine, if_exists="replace" if if_exists == "replace" else if_exists, index=False)
                row_count = len(df)
                col_count = len(df.columns)
                print(f"    [+] Successfully imported {row_count} rows and {col_count} columns into '{table_name}'")
                print(f"        Columns: {', '.join(df.columns[:8])}{'...' if len(df.columns) > 8 else ''}")
                summary.append({"sheet": sheet, "table": table_name, "rows": row_count, "cols": col_count})
            except Exception as e:
                print(f"    [!] Failed to import sheet '{sheet}': {e}")

    # Summary
    print("\n" + "=" * 55)
    print(" IMPORT SUMMARY:")
    for s in summary:
        print(f"  * Table '{s['table']}' ({s['rows']} rows, {s['cols']} columns)")
    print("=" * 55)

    # Verify tables via SQLAlchemy Inspector
    inspector = inspect(engine)
    all_tables = inspector.get_table_names() + inspector.get_view_names()
    print(f"\n[*] Verified PostgreSQL tables in database: {list(set(all_tables))}")
    print("\n[+] Your dataset is ready! MitraAI can now inspect this schema and answer NL-to-SQL queries.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Excel (.xlsx/.xls) or CSV dataset into PostgreSQL")
    parser.add_argument("file", nargs="?", help="Path to the dataset file (.xlsx, .xls, .csv)")
    parser.add_argument("--table", dest="table", help="Custom table name in PostgreSQL (e.g. students, courses)")
    parser.add_argument("--if-exists", choices=["replace", "append", "fail"], default="replace", help="How to handle existing tables")
    args = parser.parse_args()

    target_file = args.file
    if not target_file:
        # Check backend/data folder for any .xlsx, .xls, or .csv file
        data_dir = backend_dir / "data"
        if data_dir.exists():
            files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls")) + list(data_dir.glob("*.csv"))
            if files:
                target_file = str(files[0])
                print(f"Auto-detected dataset file: {target_file}")

    if not target_file:
        print("Usage:")
        print("  venv\\Scripts\\python scripts\\import_excel_to_postgres.py path\\to\\college_dataset.xlsx [--table students]")
        print("\nOr place your .xlsx/.csv file inside the 'backend\\data' directory and run without arguments.")
        sys.exit(1)

    import_file(target_file, table_override=args.table, if_exists=args.if_exists)

