import sqlite3
from config import Config

def get_db_connection():
    try:
        connection = sqlite3.connect(Config.DATABASE)
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"Error while connecting to SQLite: {e}")
        return None

def init_db():
    """Initializes the database with schema.sql"""
    try:
        conn = get_db_connection()
        if conn:
            with open('schema.sql', 'r') as f:
                schema = f.read()
                conn.executescript(schema)
            conn.commit()
            conn.close()
            print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
