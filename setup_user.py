import sqlite3
from config import Config
from werkzeug.security import generate_password_hash

def setup_user():
    try:
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT * FROM users WHERE email = 'test@example.com'")
        user = cursor.fetchone()
        
        if not user:
            print("Creating test user...")
            hashed_password = generate_password_hash('password')
            cursor.execute('''
                INSERT INTO users (full_name, email, password_hash, blood_group, city, phone, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Test User', 'test@example.com', hashed_password, 'O+', 'Test City', '1234567890', 'donor'))
            conn.commit()
            print("Test user created.")
        else:
            print("Test user already exists. Updating password...")
            hashed_password = generate_password_hash('password')
            cursor.execute("UPDATE users SET password_hash = ? WHERE email = 'test@example.com'", (hashed_password,))
            conn.commit()
            print("Password updated.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_user()
