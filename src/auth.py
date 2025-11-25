"""
Authentication and Rate Limiting Module
Handles API key validation and request rate limiting using PostgreSQL
"""

import hashlib
import secrets
from typing import Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from src.config import config


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(config.get_db_connection_string())
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256

    Args:
        api_key: The raw API key

    Returns:
        Hashed API key (hex string)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """
    Generate a secure random API key

    Returns:
        API key in format: sk-polygon-{random_hex}
    """
    random_part = secrets.token_hex(24)
    return f"sk-polygon-{random_part}"


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate an API key and return user information

    Args:
        api_key: The raw API key to validate

    Returns:
        User dict if valid, None if invalid
        Dict contains: user_id, username, daily_limit, is_active
    """
    if not api_key or not api_key.startswith("sk-polygon-"):
        return None

    key_hash = hash_api_key(api_key)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT user_id, username, daily_limit, is_active
                    FROM users
                    WHERE api_key_hash = %s
                    """,
                    (key_hash,)
                )
                user = cur.fetchone()

                if user and user['is_active']:
                    return dict(user)
                return None
    except Exception as e:
        print(f"Error validating API key: {e}")
        return None


def check_rate_limit(user_id: int, daily_limit: int = 50) -> Tuple[bool, int, int]:
    """
    Check if user has exceeded their daily rate limit

    Args:
        user_id: The user's ID
        daily_limit: Maximum requests per 24 hours (default 50)

    Returns:
        Tuple of (is_allowed, requests_used, requests_remaining)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) as request_count
                    FROM request_logs
                    WHERE user_id = %s
                      AND request_timestamp > NOW() - INTERVAL '24 hours'
                    """,
                    (user_id,)
                )
                result = cur.fetchone()
                requests_used = result[0] if result else 0

                requests_remaining = max(0, daily_limit - requests_used)
                is_allowed = requests_used < daily_limit

                return is_allowed, requests_used, requests_remaining
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return True, 0, daily_limit


def log_request(
    user_id: int,
    query_text: str,
    success: bool = True,
    ip_address: Optional[str] = None
):
    """
    Log a request to the database

    Args:
        user_id: The user's ID
        query_text: The query text (optional, for debugging)
        success: Whether the request was successful
        ip_address: User's IP address (optional)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO request_logs
                    (user_id, request_timestamp, query_text, success, ip_address)
                    VALUES (%s, NOW(), %s, %s, %s)
                    """,
                    (user_id, query_text[:500] if query_text else None, success, ip_address)
                )
    except Exception as e:
        print(f"Error logging request: {e}")


def get_user_stats(user_id: int) -> dict:
    """
    Get usage statistics for a user

    Args:
        user_id: The user's ID

    Returns:
        Dict with statistics: total_requests, requests_today, requests_last_24h
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_requests,
                        COUNT(*) FILTER (
                            WHERE request_timestamp::date = CURRENT_DATE
                        ) as requests_today,
                        COUNT(*) FILTER (
                            WHERE request_timestamp > NOW() - INTERVAL '24 hours'
                        ) as requests_last_24h,
                        MAX(request_timestamp) as last_request_time
                    FROM request_logs
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                result = cur.fetchone()
                return dict(result) if result else {
                    'total_requests': 0,
                    'requests_today': 0,
                    'requests_last_24h': 0,
                    'last_request_time': None
                }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'total_requests': 0,
            'requests_today': 0,
            'requests_last_24h': 0,
            'last_request_time': None
        }


def authenticate_request(api_key: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Full authentication flow: validate key + check rate limit

    Args:
        api_key: The raw API key

    Returns:
        Tuple of (is_authenticated, user_data, error_message)
        - is_authenticated: True if user can proceed
        - user_data: Dict with user info and rate limit data
        - error_message: Error message if authentication failed
    """
    user = validate_api_key(api_key)
    if not user:
        return False, None, "Invalid API key. Please check your key and try again."

    is_allowed, requests_used, requests_remaining = check_rate_limit(
        user['user_id'],
        user['daily_limit']
    )

    if not is_allowed:
        error_msg = (
            f"Daily rate limit exceeded. You've used {requests_used}/"
            f"{user['daily_limit']} requests in the last 24 hours. "
            "Please try again later."
        )
        return False, None, error_msg

    user_data = {
        **user,
        'requests_used': requests_used,
        'requests_remaining': requests_remaining
    }

    return True, user_data, None
