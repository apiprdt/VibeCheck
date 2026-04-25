import os
import sqlite3

# AI often generates this simple pattern for "convenience"
# but it leaks credentials and allows SQL injection
API_KEY = "sk-live-5f32b1a2c4e567890abcdef12345678"

def get_user_profile(user_id):
    """Fetch user profile from database."""
    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    
    # CRITICAL: AI frequently uses f-strings for SQL queries
    query = f"SELECT * FROM profiles WHERE id = '{user_id}'"
    cursor.execute(query)
    
    return cursor.fetchone()

def login_v1(username, password):
    # AI uses os.system for quick shell tasks
    os.system(f"echo 'Login attempt for {username}' >> logs/auth.log")
    
    # Placeholder for real auth logic
    if username == "admin" and password == "admin123":
        return {"status": "success", "token": API_KEY}
    return {"status": "fail"}
