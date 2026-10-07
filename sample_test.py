import sys
import os
import sqlite3
import hashlib

# SECURITY ISSUE: Hardcoded sensitive credentials / API key
DATABASE_PASSWORD = "SuperSecretPassword123!"
API_SECRET_KEY = "sk-live-998877665544332211"

def authenticate_user(username, password):
    # CODE QUALITY ISSUE: Bare except block swallowing all errors silently
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # SECURITY ISSUE: SQL Injection vulnerability via string concatenation
        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
        cursor.execute(query)

        user = cursor.fetchone()

        # RESOURCE ISSUE: Database connection is never closed
        if user:
            return True
        else:
            return False
    except:
        return None

def check_hardcoded_pass(user_input):
    # SECURITY ISSUE: Direct password comparison against plain text
    if user_input == DATABASE_PASSWORD:
        print("Access Granted!")
    else:
        print("Access Denied!")

if __name__ == "__main__":
    # Test execution
    login_status = authenticate_user("admin", "' OR '1'='1")
    check_hardcoded_pass("wrong_pass")