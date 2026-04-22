import sqlite3
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

def verify_user():
    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = 'test@example.com'")
        user = cursor.fetchone()
        
        if user:
            print(f"User found: {user['email']}")
            print(f"Password hash: {user['password_hash']}")
            is_valid = check_password_hash(user['password_hash'], 'password')
            print(f"Password 'password' is valid: {is_valid}")
        else:
            print("User not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_user()
