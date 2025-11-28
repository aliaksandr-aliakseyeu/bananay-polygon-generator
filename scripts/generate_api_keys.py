"""
Generate API keys for initial users
Creates 3 users with API keys for MVP
"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2  # noqa: E402
from src.config import config  # noqa: E402
from src.auth import generate_api_key, hash_api_key  # noqa: E402


def create_user(cursor, username: str, email: str = None, daily_limit: int = 50, notes: str = None):
    """Create a user and return their API key"""

    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    cursor.execute(
        """
        INSERT INTO users (username, email, api_key_hash, daily_limit, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING user_id
        """,
        (username, email, api_key_hash, daily_limit, notes)
    )

    user_id = cursor.fetchone()[0]

    return user_id, api_key


def generate_initial_users():
    """Generate 3 initial users for MVP"""
    print("[API KEYS] Generating API keys for initial users...")
    print()

    try:
        conn = psycopg2.connect(config.get_db_connection_string())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"[WARNING] {existing_count} user(s) already exist in database")
            response = input("Do you want to create additional users? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Aborted.")
                return
            print()

        users_to_create = [
            {
                "username": "admin",
                "email": "gollum80@gmail.com",
                "daily_limit": 50,
                "notes": "Initial MVP user #1"
            },
            {
                "username": "ceo",
                "email": "",
                "daily_limit": 50,
                "notes": "Initial MVP user #2"
            },
            {
                "username": "alex",
                "email": "",
                "daily_limit": 50,
                "notes": "Initial MVP user #3"
            }
        ]

        print("Creating users:")
        print("-" * 80)

        created_users = []

        for user_data in users_to_create:
            try:
                user_id, api_key = create_user(
                    cursor,
                    username=user_data["username"],
                    email=user_data["email"],
                    daily_limit=user_data["daily_limit"],
                    notes=user_data["notes"]
                )

                created_users.append({
                    "user_id": user_id,
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "api_key": api_key,
                    "daily_limit": user_data["daily_limit"]
                })

                print(f"[OK] Created user: {user_data['username']}")

            except psycopg2.IntegrityError as e:
                if "unique constraint" in str(e).lower():
                    print(f"[SKIP] {user_data['username']}: Already exists")
                    conn.rollback()
                else:
                    raise

        conn.commit()
        cursor.close()
        conn.close()

        if not created_users:
            print("\n[INFO] No new users were created")
            return

        print()
        print("=" * 80)
        print("  API Keys Generated Successfully!")
        print("=" * 80)
        print()
        print("[IMPORTANT] Save these API keys securely. They won't be shown again!")
        print()

        for user in created_users:
            print(f"[USER] {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   API Key: {user['api_key']}")
            print(f"   Daily Limit: {user['daily_limit']} requests")
            print()

        print("=" * 80)
        print()
        print("[NEXT STEPS]")
        print("  1. Send each user their API key via secure channel (email, password manager)")
        print("  2. Users should paste the key in the Streamlit app sidebar")
        print("  3. Keys are hashed in database - if lost, you'll need to regenerate")
        print()

        backup_file = "api_keys_backup.txt"
        with open(backup_file, "w") as f:
            f.write("Polygon Generator - API Keys\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {os.popen('date').read().strip()}\n")
            f.write("=" * 80 + "\n\n")

            for user in created_users:
                f.write(f"User: {user['username']}\n")
                f.write(f"Email: {user['email']}\n")
                f.write(f"API Key: {user['api_key']}\n")
                f.write(f"Daily Limit: {user['daily_limit']} requests\n")
                f.write("-" * 80 + "\n\n")

        print(f"[SAVED] API keys also saved to: {backup_file}")
        print("   (Delete this file after distributing keys!)")
        print()

    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        print("\nMake sure you ran 'python scripts/init_database.py' first!")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("  Polygon Generator - API Key Generation")
    print("=" * 80)
    print()
    generate_initial_users()
