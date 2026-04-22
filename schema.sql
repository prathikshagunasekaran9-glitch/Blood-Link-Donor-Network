CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    city TEXT NOT NULL,
    phone TEXT NOT NULL,
    date_of_birth DATE,
    age INTEGER,
    last_donation_date DATE,
    role TEXT DEFAULT 'donor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    patient_name TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    units_needed INTEGER NOT NULL,
    hospital_name TEXT NOT NULL,
    city TEXT NOT NULL,
    contact_phone TEXT NOT NULL,
    urgency TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    request_id INTEGER NOT NULL,
    donation_date DATE NOT NULL,
    status TEXT DEFAULT 'scheduled',
    FOREIGN KEY (donor_id) REFERENCES users(id),
    FOREIGN KEY (request_id) REFERENCES requests(id)
);
