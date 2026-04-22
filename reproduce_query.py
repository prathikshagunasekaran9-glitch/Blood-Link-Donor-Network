import sqlite3
from config import Config

def check_query():
    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, u.full_name as donor_name, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            ORDER BY d.donation_date DESC
        '''
        
        print("Executing query...")
        cursor.execute(query)
        donations = cursor.fetchall()
        print(f"Found {len(donations)} donations.")
        
        if donations:
            first = donations[0]
            print("First donation keys:", first.keys())
            print("First donation values:", dict(first))
            
            # Check access
            print("donor_name:", first['donor_name'])
            print("patient_name:", first['patient_name'])
            print("donation_date:", first['donation_date'])
            print("status:", first['status'])
            print("id:", first['id'])
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_query()
