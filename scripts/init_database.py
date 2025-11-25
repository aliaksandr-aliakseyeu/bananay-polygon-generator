"""
Initialize the database schema for authentication
Run this script once to set up the database tables
"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2  # noqa: E402
from src.config import config  # noqa: E402


def init_database():
    """Initialize database schema from SQL file"""
    print("[DATABASE] Initializing database schema...")

    try:
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'db_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = psycopg2.connect(config.get_db_connection_string())
        cursor = conn.cursor()

        print(f"[OK] Connected to database: {config.POSTGRES_DB}")

        cursor.execute(schema_sql)
        conn.commit()

        print("[SUCCESS] Database schema created successfully!")
        print("\nCreated tables:")
        print("  - users (stores API keys and user info)")
        print("  - request_logs (tracks requests for rate limiting)")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('users', 'request_logs')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if len(tables) == 2:
            print("\n[OK] Verification passed: All tables created")
        else:
            print(f"\n[WARNING] Expected 2 tables, found {len(tables)}")

        cursor.close()
        conn.close()

        print("\n[COMPLETE] Database initialization complete!")
        print("\nNext step: Run 'python scripts/generate_api_keys.py' to create users")

    except FileNotFoundError:
        print("[ERROR] db_schema.sql not found")
        print(f"   Expected location: {schema_path}")
        sys.exit(1)

    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL running?")
        print("  2. Are your database credentials correct in .env?")
        print("  3. Does the database exist?")
        print("\nConnection details:")
        print(f"  Host: {config.POSTGRES_HOST}")
        print(f"  Port: {config.POSTGRES_PORT}")
        print(f"  Database: {config.POSTGRES_DB}")
        print(f"  User: {config.POSTGRES_USER}")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("  Polygon Generator - Database Initialization")
    print("=" * 60)
    print()
    init_database()
