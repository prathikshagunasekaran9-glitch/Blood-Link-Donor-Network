import sqlite3
from config import Config

def check_db():
    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("--- Users ---")
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for u in users:
            print(dict(u))
            
        print("\n--- Requests ---")
        cursor.execute("SELECT * FROM requests")
        requests = cursor.fetchall()
        for r in requests:
            print(dict(r))
            
        print("\n--- Donations ---")
        cursor.execute("SELECT * FROM donations")
        donations = cursor.fetchall()
        for d in donations:
            print(dict(d))
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
