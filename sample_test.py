"""User authentication and credential validation testing module."""

import os
import secrets
import sqlite3
from typing import Optional

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")


def authenticate_user(username: str, password: str) -> Optional[bool]:
    """Authenticate user credentials safely using parameterized database queries."""
    try:
        # Use context manager to ensure DB connections close automatically
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            # Parameterized query prevents SQL Injection
            query = "SELECT * FROM users WHERE username = ? AND password = ?"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            return bool(user)
    except sqlite3.Error as err:
        print(f"Database authentication error: {err}")
        return None


def check_hardcoded_pass(user_input: str) -> None:
    """Validate password input using constant-time string comparison."""
    if not DATABASE_PASSWORD:
        print("Access Denied: DATABASE_PASSWORD environment variable not set.")
        return

    if secrets.compare_digest(user_input, DATABASE_PASSWORD):
        print("Access Granted!")
    else:
        print("Access Denied!")


if __name__ == "__main__":
    login_status = authenticate_user("admin", "secure_password_123")
    check_hardcoded_pass("sample_password")
