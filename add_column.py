import sqlite3
from config import Config

def add_column():
    try:
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE requests ADD COLUMN request_reference_id TEXT")
        conn.commit()
        conn.close()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
