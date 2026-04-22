import sqlite3
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random
from config import Config

# Constants for realistic data
NAMES = [
    "Aarav", "Vihaan", "Aditya", "Sai", "Ishaan", "Rohan", "Karthik", "Rahul", "Arjun", "Vikram",
    "Suresh", "Ramesh", "Ganesh", "Dinesh", "Mahesh", "Vijay", "Ajith", "Surya", "Kavin", "Bala",
    "Diya", "Ananya", "Saanvi", "Myra", "Aadhya", "Neha", "Priya", "Divya", "Kavya", "Lakshmi",
    "Meena", "Swathi", "Deepa", "Shalini", "Nithya", "Revathi", "Geetha", "Sangeetha", "Anitha"
]

LAST_NAMES = [
    "Patel", "Rao", "Kumar", "Krishna", "Sharma", "Gupta", "Reddy", "Singh", "Mehta", "Nair",
    "Verma", "Iyer", "Joshi", "Malhotra", "Deshmukh", "Gounder", "Mudaliar", "Pillai", "Chettiar", "Nadar"
]

CITIES = [
    "Erode", "Salem", "Dharmapuri", "Chennai", "Coimbatore", 
    "Sathyamangalam", "Gobichettipalayam", "Anthiyur", "Pariyur", "Madurai", "Tiruchirappalli", "Tiruppur"
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

HOSPITALS = [
    "Apollo Hospital", "Fortis Hospital", "Max Healthcare", "Manipal Hospital", 
    "City General Hospital", "Global Health City", "MIOT Hospital", "KMCH", "Ganga Hospital"
]

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def populate_users(cursor):
    print("Populating users...")
    users = []
    
    # Ensure coverage: Each city gets at least one donor of each blood group
    for city in CITIES:
        for bg in BLOOD_GROUPS:
            first_name = random.choice(NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1, 9999)}@example.com"
            password_hash = generate_password_hash("password123")
            phone = f"9{random.randint(100000000, 999999999)}"
            dob = date(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28))
            age = date.today().year - dob.year
            
            try:
                cursor.execute('''
                    INSERT INTO users (full_name, email, password_hash, blood_group, city, phone, date_of_birth, age)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (full_name, email, password_hash, bg, city, phone, dob, age))
                users.append(cursor.lastrowid)
            except sqlite3.IntegrityError:
                print(f"User {email} already exists, skipping.")
                
    return users

def clear_data(cursor):
    print("Clearing existing requests and donations...")
    cursor.execute("DELETE FROM requests")
    cursor.execute("DELETE FROM donations")
    print("Data cleared.")

def populate_requests(cursor, user_ids):
    print("Populating requests...")
    request_ids = []
    for _ in range(20):
        requester_id = random.choice(user_ids)
        patient_name = f"{random.choice(NAMES).split()[0]} {random.choice(LAST_NAMES)}"
        blood_group = random.choice(BLOOD_GROUPS)
        units = random.randint(1, 5)
        hospital = random.choice(HOSPITALS)
        city = random.choice(CITIES)
        phone = f"8{random.randint(100000000, 999999999)}"
        urgency = random.choice(['normal', 'critical', 'urgent'])
        
        cursor.execute('''
            INSERT INTO requests (requester_id, patient_name, blood_group, units_needed, hospital_name, city, contact_phone, urgency, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (requester_id, patient_name, blood_group, units, hospital, city, phone, urgency))
        request_ids.append(cursor.lastrowid)
    return request_ids

def populate_donations(cursor, user_ids, request_ids):
    print("Populating donations...")
    for _ in range(20):
        donor_id = random.choice(user_ids)
        request_id = random.choice(request_ids)
        donation_date = date.today() - timedelta(days=random.randint(0, 30))
        status = random.choice(['scheduled', 'completed', 'cancelled'])
        
        cursor.execute('''
            INSERT INTO donations (donor_id, request_id, donation_date, status)
            VALUES (?, ?, ?, ?)
        ''', (donor_id, request_id, donation_date, status))

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        clear_data(cursor)
        user_ids = populate_users(cursor)
        if user_ids:
            request_ids = populate_requests(cursor, user_ids)
            if request_ids:
                populate_donations(cursor, user_ids, request_ids)
            conn.commit()
            print("Database populated successfully!")
        else:
            print("No users created or found.")
    except Exception as e:
        print(f"Error populating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
