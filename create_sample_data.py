import sqlite3
from datetime import date

def create_sample_data():
    conn = sqlite3.connect('blood_donor.db')
    cursor = conn.cursor()
    
    # 1. Find the user "Prathiksha G"
    cursor.execute("SELECT id FROM users WHERE full_name LIKE '%Prathiksha G%'")
    user = cursor.fetchone()
    
    if not user:
        print("User 'Prathiksha G' not found. Creating a dummy user.")
        cursor.execute("INSERT INTO users (full_name, email, password_hash, blood_group, city, phone) VALUES (?, ?, ?, ?, ?, ?)",
                       ('Prathiksha G', 'prathiksha@example.com', 'hash', 'O+', 'Chennai', '1234567890'))
        user_id = cursor.lastrowid
    else:
        user_id = user[0]
        print(f"Found user 'Prathiksha G' with ID: {user_id}")

    # 2. Create a sample request (if not exists)
    # Let's create a request from someone else so Prathiksha can donate to it
    cursor.execute("INSERT INTO requests (requester_id, patient_name, blood_group, units_needed, hospital_name, city, contact_phone, urgency, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (user_id, 'Prathiksha G', 'O+', 2, 'City Hospital', 'Chennai', '9876543210', 'urgent', 'pending'))
    request_id = cursor.lastrowid
    print(f"Created sample request with ID: {request_id}")
    
    # 3. Create a donation record for Prathiksha G
    today = date.today()
    cursor.execute("INSERT INTO donations (donor_id, request_id, donation_date, status) VALUES (?, ?, ?, ?)",
                   (user_id, request_id, today, 'completed'))
    print(f"Created donation record for user {user_id} on request {request_id}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_sample_data()
