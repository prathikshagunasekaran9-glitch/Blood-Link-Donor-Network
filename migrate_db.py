"""
Database Migration Script
Adds new columns to the users table for enhanced donor registration
"""
import sqlite3
from config import Config

def migrate_database():
    """Add new columns to existing users table"""
    try:
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add date_of_birth column if it doesn't exist
        if 'date_of_birth' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN date_of_birth DATE")
            print("✓ Added date_of_birth column")
        else:
            print("✓ date_of_birth column already exists")
        
        # Add age column if it doesn't exist
        if 'age' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER")
            print("✓ Added age column")
        else:
            print("✓ age column already exists")
        
        # Add last_donation_date column if it doesn't exist
        if 'last_donation_date' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_donation_date DATE")
            print("✓ Added last_donation_date column")
        else:
            print("✓ last_donation_date column already exists")
        
        conn.commit()
        conn.close()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_database()
