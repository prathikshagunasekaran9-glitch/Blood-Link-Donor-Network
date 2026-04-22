import sqlite3
from config import Config

def add_status_column():
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        print("Column 'status' added successfully.")
        
        # Verify
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'status':
                print("Verification: status column exists.")
                
        conn.commit()
    except Exception as e:
        print(f"Error (column might already exist): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_status_column()
