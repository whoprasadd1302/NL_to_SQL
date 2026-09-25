import os
import sys
from dotenv import load_dotenv

# Load env variables from backend/.env
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
dbname = os.getenv("POSTGRES_DB", "mitraai")

print(f"Testing PostgreSQL connection to {host}:{port} with user '{user}'...")

try:
    # 1. Connect to default 'postgres' database to verify credentials
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    print(" Authentication successful!")

    # 2. Check if target database exists, if not create it
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cursor.fetchone()
    if not exists:
        print(f"Database '{dbname}' does not exist. Creating database '{dbname}'...")
        cursor.execute(f'CREATE DATABASE "{dbname}"')
        print(f" Database '{dbname}' created successfully.")
    else:
        print(f" Database '{dbname}' exists.")

    cursor.close()
    conn.close()

    # 3. Connect to target database and list tables
    target_conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    t_cur = target_conn.cursor()
    t_cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = t_cur.fetchall()
    print(f"\nConnected to '{dbname}' successfully!")
    if tables:
        print("Existing tables in database:")
        for t in tables:
            print(f"  - {t[0]}")
    else:
        print("No user tables found yet. Ready to create/import your college dataset!")
    
    t_cur.close()
    target_conn.close()

except Exception as e:
    print(f"\n PostgreSQL Connection Error: {e}")
    print("\nPlease verify:")
    print("1. Your PostgreSQL password is set in backend/.env (POSTGRES_PASSWORD=...)")
    print(f"2. PostgreSQL service is running on {host}:{port}")
    sys.exit(1)
