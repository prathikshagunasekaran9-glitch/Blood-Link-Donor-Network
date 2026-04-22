from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from db import get_db_connection, init_db
from werkzeug.security import generate_password_hash, check_password_hash
import functools
import os
import io
import random
import qrcode
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from flask import send_file
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB on first run
try:
    init_db()
except:
    pass

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/admin'):
                return redirect(url_for('admin_login'))
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        blood_group = request.form['blood_group']
        city = request.form['city']
        phone = request.form['phone']
        date_of_birth = request.form.get('date_of_birth', '')
        last_donation_date = request.form.get('last_donation_date', '')
        
        # Calculate age from date of birth
        age = None
        if date_of_birth:
            from datetime import datetime
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                today = datetime.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                flash('Invalid date of birth format.', 'error')
                return render_template('register.html')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                flash('Email already exists.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                
                # Handle optional last_donation_date
                if last_donation_date == '':
                    last_donation_date = None
                
                cursor.execute('''
                    INSERT INTO users (full_name, email, password_hash, blood_group, city, phone, 
                                     date_of_birth, age, last_donation_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (full_name, email, hashed_password, blood_group, city, phone, 
                      date_of_birth if date_of_birth else None, age, last_donation_date))
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                conn.close()
                return redirect(url_for('login'))
            conn.close()
        else:
            flash('Database connection failed.', 'error')
            
    return render_template('register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                if user['role'] == 'admin':
                    session['user_id'] = user['id']
                    session['user_name'] = user['full_name']
                    session['role'] = user['role']
                    flash('Admin logged in successfully!', 'success')
                    return redirect(url_for('admin'))
                else:
                    flash('Access denied. You are not an admin.', 'error')
            else:
                flash('Invalid credentials.', 'error')
        else:
            flash('Database connection failed.', 'error')
            
    return render_template('admin_login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['role'] = user['role']
                flash('Logged in successfully!', 'success')
                conn.close()
                
                if user['role'] == 'admin':
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')
            conn.close()
        else:
            flash('Database connection failed.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    stats = {
        'total_donors': 0,
        'total_requests': 0,
        'total_donations': 0,
        'blood_groups': {'labels': [], 'data': []},
        'urgency': {'labels': [], 'data': []},
        'donation_status': {'labels': [], 'data': []}
    }
    
    if conn:
        cursor = conn.cursor()
        
        # Total Donors
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'donor'")
        stats['total_donors'] = cursor.fetchone()[0]
        
        # Total Requests
        cursor.execute("SELECT COUNT(*) FROM requests")
        stats['total_requests'] = cursor.fetchone()[0]
        
        # Total Donations
        cursor.execute("SELECT COUNT(*) FROM donations")
        stats['total_donations'] = cursor.fetchone()[0]
        
        # Blood Group Distribution
        cursor.execute("SELECT blood_group, COUNT(*) FROM users WHERE role='donor' GROUP BY blood_group")
        bg_data = cursor.fetchall()
        stats['blood_groups']['labels'] = [row[0] for row in bg_data]
        stats['blood_groups']['data'] = [row[1] for row in bg_data]
        
        # Request Urgency
        cursor.execute("SELECT urgency, COUNT(*) FROM requests GROUP BY urgency")
        urgency_data = cursor.fetchall()
        stats['urgency']['labels'] = [row[0] for row in urgency_data]
        stats['urgency']['data'] = [row[1] for row in urgency_data]
        
        # Donation Status
        cursor.execute("SELECT status, COUNT(*) FROM donations GROUP BY status")
        status_data = cursor.fetchall()
        stats['donation_status']['labels'] = [row[0] for row in status_data]
        stats['donation_status']['data'] = [row[1] for row in status_data]
        
    if conn:
        cursor = conn.cursor()
        
        # Stats Queries (Existing logic preserved)
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'donor'")
        stats['total_donors'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM requests")
        stats['total_requests'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM donations WHERE status='completed'") # Updated to completed as requested
        stats['total_donations'] = cursor.fetchone()[0]
        
        # Blood Group Distribution
        cursor.execute("SELECT blood_group, COUNT(*) FROM users WHERE role='donor' GROUP BY blood_group")
        bg_data = cursor.fetchall()
        stats['blood_groups']['labels'] = [row[0] for row in bg_data]
        stats['blood_groups']['data'] = [row[1] for row in bg_data]
        
        # Request Urgency
        cursor.execute("SELECT urgency, COUNT(*) FROM requests GROUP BY urgency")
        urgency_data = cursor.fetchall()
        stats['urgency']['labels'] = [row[0] for row in urgency_data]
        stats['urgency']['data'] = [row[1] for row in urgency_data]
        
        # Donation Status
        cursor.execute("SELECT status, COUNT(*) FROM donations GROUP BY status")
        status_data = cursor.fetchall()
        stats['donation_status']['labels'] = [row[0] for row in status_data]
        stats['donation_status']['data'] = [row[1] for row in status_data]
        
        # Fetch Lists for Admin Management
        cursor.execute("SELECT * FROM users WHERE role != 'admin'") 
        users = cursor.fetchall()
        
        cursor.execute("SELECT * FROM requests ORDER BY created_at DESC")
        requests_list = cursor.fetchall()
        
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.email as donor_email, r.patient_name 
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            ORDER BY d.donation_date DESC
        ''')
        donations = cursor.fetchall()
        
        conn.close()
        
    return render_template('dashboard.html', stats=stats, users=users, requests=requests_list, donations=donations)

@app.route('/search')
def search():
    donors = []
    blood_group = request.args.get('blood_group')
    city = request.args.get('city')
    
    if blood_group or city:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "SELECT * FROM users WHERE role = 'donor'"
            params = []
            
            if blood_group:
                query += " AND blood_group = ?"
                params.append(blood_group)
            
            if city:
                query += " AND city LIKE ?"
                params.append(f"%{city}%")
                
            cursor.execute(query, tuple(params))
            donors = cursor.fetchall()
            conn.close()
            
    return render_template('search.html', donors=donors)


@app.route('/all_donors')
def all_donors():
    conn = get_db_connection()
    donors = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'donor' ORDER BY full_name ASC")
        donors = cursor.fetchall()
        conn.close()
    return render_template('all_donors.html', donors=donors)



@app.route('/request_blood', methods=['GET', 'POST'])
@login_required
def request_blood():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        blood_group = request.form['blood_group']
        units_needed = request.form['units_needed']
        hospital_name = request.form['hospital_name']
        city = request.form['city']
        contact_phone = request.form['contact_phone']
        urgency = request.form['urgency']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO requests (requester_id, patient_name, blood_group, units_needed, hospital_name, city, contact_phone, urgency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], patient_name, blood_group, units_needed, hospital_name, city, contact_phone, urgency))
            conn.commit()
            conn.close()
            flash('Blood request submitted successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Database connection failed.', 'error')
            
    return render_template('request_blood.html')

@app.route('/admin/block_user/<int:user_id>')
@login_required
def admin_block_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'blocked' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        flash('User blocked successfully.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/admin/unblock_user/<int:user_id>')
@login_required
def admin_unblock_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'active' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        flash('User unblocked successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Also delete related requests and donations? Or keep for history?
        # Usually keep history but anonymize, or cascade delete.
        # Simple delete for now as requested.
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        flash('User deleted successfully.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/admin/approve_request/<int:request_id>')
@login_required
def admin_approve_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = 'approved' WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()
        flash('Request approved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/reject_request/<int:request_id>')
@login_required
def admin_reject_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = 'rejected' WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()
        flash('Request rejected.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/admin/complete_donation/<int:donation_id>')
@login_required
def admin_complete_donation(donation_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE donations SET status = 'completed' WHERE id = ?", (donation_id,))
        
        # Determine email success by attempting to send immediately (Direct Send)
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.email as donor_email, u.blood_group, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            WHERE d.id = ?
        ''', (donation_id,))
        donation = cursor.fetchone()
        
        email_sent = False
        if donation:
            try:
                # Direct Send Logic
                pdf_buffer = generate_certificate_pdf(donation)
                pdf_bytes = pdf_buffer.getvalue()
                subject = f"Blood Donation Certificate - {donation['donor_name']}"
                body = f"""Dear {donation['donor_name']},

Thank you for your generous blood donation. Your contribution has helped save lives.

Please find your donation certificate attached.

Best regards,
BloodLink Team
"""
                filename = f"certificate_{donation['id']}.pdf"
                send_email_with_attachment(donation['donor_email'], subject, body, pdf_bytes, filename)
                email_sent = True
            except Exception as e:
                print(f"Direct send failed: {e}")
        
        conn.commit()
        conn.close()
        
        if email_sent:
            if app.config['MAIL_SERVER'] == 'localhost':
                flash('Status updated! (TEST MODE: Email saved to internal logs, NOT sent to real user. See "View Log")', 'warning')
            else:
                flash(f'Donation marked Completed & Certificate emailed to {donation["donor_email"]}!', 'success')
        else:
            flash('Donation Completed. (Certificate email failed - check App Password)', 'error')
            
    return redirect(url_for('dashboard'))

@app.route('/admin/email_logs')
@login_required
def view_email_logs():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    logs = ""
    try:
        if os.path.exists("sent_emails.txt"):
            with open("sent_emails.txt", "r", encoding='utf-8', errors='ignore') as f:
                logs = f.read()
    except Exception as e:
        logs = f"Error reading log file: {e}"
        
    return render_template('email_logs.html', logs=logs)

@app.route('/admin/clear_email_logs', methods=['POST'])
@login_required
def clear_email_logs():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    try:
        if os.path.exists("sent_emails.txt"):
            open("sent_emails.txt", "w").close() # Clear file
            flash('Email logs cleared.', 'success')
    except Exception as e:
        flash(f'Error clearing logs: {e}', 'error')
        
    return redirect(url_for('view_email_logs'))
        
@app.route('/admin/send_certificate/<int:donation_id>')
@login_required
def prep_send_certificate_email(donation_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    donation = None
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.email as donor_email, u.blood_group, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            WHERE d.id = ?
        ''', (donation_id,))
        donation = cursor.fetchone()
        conn.close()
    
    if not donation:
        flash('Donation record not found.', 'error')
        return redirect(url_for('dashboard'))
        
    return render_template('send_certificate.html', donation=donation)

@app.route('/admin/confirm_send_email/<int:donation_id>', methods=['POST'])
@login_required
def admin_confirm_send_email(donation_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
        
    subject = request.form.get('subject')
    body = request.form.get('body')
    
    conn = get_db_connection()
    donation = None
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.email as donor_email, u.blood_group, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            WHERE d.id = ?
        ''', (donation_id,))
        donation = cursor.fetchone()
        conn.close()
        
    if donation:
        try:
            pdf_buffer = generate_certificate_pdf(donation)
            pdf_bytes = pdf_buffer.getvalue()
            filename = f"certificate_{donation['id']}.pdf"
            
            send_email_with_attachment(donation['donor_email'], subject, body, pdf_bytes, filename)
            flash(f'Certificate emailed successfully to {donation["donor_email"]}!', 'success')
        except Exception as e:
            flash(f'Failed to send email: {e}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/update_donor', methods=['GET', 'POST'])
@login_required
def update_donor():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'error')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        city = request.form['city']
        date_of_birth = request.form.get('date_of_birth', '')
        last_donation_date = request.form.get('last_donation_date', '')
        
        # Calculate age from date of birth
        age = None
        if date_of_birth:
            from datetime import datetime
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                today = datetime.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                flash('Invalid date of birth format.', 'error')
                cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
                donor = cursor.fetchone()
                conn.close()
                return render_template('update_donor.html', donor=donor)
        
        # Check if email is already used by another user
        cursor.execute('SELECT * FROM users WHERE email = ? AND id != ?', (email, session['user_id']))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Email already exists.', 'error')
            cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
            donor = cursor.fetchone()
            conn.close()
            return render_template('update_donor.html', donor=donor)
        
        # Handle optional last_donation_date
        if last_donation_date == '':
            last_donation_date = None
        
        # Update user information
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, blood_group = ?, city = ?, 
                date_of_birth = ?, age = ?, last_donation_date = ?
            WHERE id = ?
        ''', (full_name, email, phone, blood_group, city, 
              date_of_birth if date_of_birth else None, age, last_donation_date, 
              session['user_id']))
        
        conn.commit()
        conn.close()
        
        # Update session name if changed
        session['user_name'] = full_name
        
        flash('Your information has been updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request - display form with current data
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    donor = cursor.fetchone()
    conn.close()
    
    if not donor:
        flash('Donor not found.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('update_donor.html', donor=donor)

@app.route('/admin')
@login_required
def admin():
    if session.get('role') != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    users = []
    requests = []
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT * FROM requests ORDER BY created_at DESC')
        requests = cursor.fetchall()
        conn.close()
        
    return render_template('admin.html', users=users, requests=requests)

@app.route('/requests')
@login_required
def requests_list():
    conn = get_db_connection()
    requests = []
    if conn:
        cursor = conn.cursor()
        # Get all pending requests that are not fulfilled
        cursor.execute('''
            SELECT * FROM requests 
            WHERE status = 'pending' 
            ORDER BY 
                CASE urgency 
                    WHEN 'critical' THEN 1 
                    WHEN 'urgent' THEN 2 
                    ELSE 3 
                END,
                created_at DESC
        ''')
        requests = cursor.fetchall()
        conn.close()
    return render_template('requests.html', requests=requests)

@app.route('/donate/<int:request_id>', methods=['POST'])
@login_required
def donate(request_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Check if request exists and is still pending
        cursor.execute('SELECT * FROM requests WHERE id = ? AND status = "pending"', (request_id,))
        req = cursor.fetchone()
        
        if req:
            # Create donation record
            from datetime import date
            today = date.today()
            
            cursor.execute('''
                INSERT INTO donations (donor_id, request_id, donation_date, status)
                VALUES (?, ?, ?, 'scheduled')
            ''', (session['user_id'], request_id, today))
            
            conn.commit()
            flash('Thank you! Your donation has been scheduled. Please contact the requester.', 'success')
        else:
            flash('Request not found or no longer active.', 'error')
            
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/create_donation_record', methods=['GET', 'POST'])
@login_required
def create_donation_record():
    if request.method == 'POST':
        donor_id = request.form['donor_id']
        request_id = request.form['request_id']
        donation_date = request.form['donation_date']
        status = request.form['status']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO donations (donor_id, request_id, donation_date, status)
                    VALUES (?, ?, ?, ?)
                ''', (donor_id, request_id, donation_date, status))
                conn.commit()
                new_id = cursor.lastrowid
                flash('Donation record created successfully.', 'success')
                
                if status == 'completed':
                    # Do NOT email automatically. Admin will do it manually.
                    return redirect(url_for('create_donation_record', certificate_id=new_id))
                else:
                    return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Error creating record: {e}', 'error')
            finally:
                conn.close()
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    users = []
    requests_list = []
    certificate_id = request.args.get('certificate_id')
    
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT * FROM requests ORDER BY created_at DESC')
        requests_list = cursor.fetchall()
        conn.close()
        
    return render_template('create_donation_record.html', users=users, requests=requests_list, certificate_id=certificate_id)

@app.route('/recent_donations')
@login_required
def recent_donations():
    conn = get_db_connection()
    donations = []
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            ORDER BY d.donation_date DESC
        ''')
        donations = cursor.fetchall()
        conn.close()
    return render_template('recent_donations.html', donations=donations)

@app.route('/donation/<int:donation_id>')
@login_required
def donation_details(donation_id):
    conn = get_db_connection()
    donation = None
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
        donation = cursor.fetchone()
        conn.close()
    
    if not donation:
        flash('Donation record not found.', 'error')
        return redirect(url_for('recent_donations'))
        
    return render_template('donation_details.html', donation=donation)

@app.route('/certificate/<int:donation_id>')
@login_required
def download_certificate(donation_id):
    conn = get_db_connection()
    donation = None
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.blood_group, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            WHERE d.id = ?
        ''', (donation_id,))
        donation = cursor.fetchone()
        conn.close()
    
    if not donation:
        flash('Donation record not found.', 'error')
        return redirect(url_for('recent_donations'))
        
    if donation['status'] != 'completed':
        flash('Certificate is only available for completed donations.', 'error')
        return redirect(url_for('recent_donations'))

    pdf_buffer = generate_certificate_pdf(donation)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"certificate_{donation['id']}.pdf", mimetype='application/pdf')

@app.route('/send_certificate_email/<int:donation_id>')
@login_required
def send_certificate_email(donation_id):
    conn = get_db_connection()
    donation = None
    donor_email = None
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.full_name as donor_name, u.email as donor_email, u.blood_group, r.patient_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            JOIN requests r ON d.request_id = r.id
            WHERE d.id = ?
        ''', (donation_id,))
        donation = cursor.fetchone()
        if donation:
            donor_email = donation['donor_email']
        conn.close()
    
    if not donation:
        flash('Donation record not found.', 'error')
        return redirect(url_for('recent_donations'))

    if donation['status'] != 'completed':
        flash('Certificate is only available for completed donations.', 'error')
        return redirect(url_for('recent_donations'))

    try:
        pdf_buffer = generate_certificate_pdf(donation)
        pdf_bytes = pdf_buffer.getvalue()
        
        subject = f"Blood Donation Certificate - {donation['donor_name']}"
        body = f"""Dear {donation['donor_name']},

Thank you for your generous blood donation. Your contribution has helped save lives.

Please find your donation certificate attached.

Best regards,
BloodLink Team
"""
        filename = f"certificate_{donation['id']}.pdf"
        
        send_email_with_attachment(donor_email, subject, body, pdf_bytes, filename)
        flash(f'Certificate emailed successfully to {donor_email}!', 'success')
    except Exception as e:
        flash(f'Failed to send email: {e}', 'error')
        # print(f"Email error: {e}") # Debug

    return redirect(url_for('recent_donations'))

def generate_certificate_pdf(donation):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=portrait(letter))
    width, height = portrait(letter)
    
    # Colors
    gold_color = colors.Color(0.7, 0.5, 0.2) # Approximate gold/brown
    red_color = colors.Color(0.7, 0.1, 0.1) # Darker red
    
    # 1. Decorative Border
    c.setStrokeColor(gold_color)
    c.setLineWidth(3)
    c.rect(20, 20, width-40, height-40) # Outer
    c.setLineWidth(1)
    c.rect(25, 25, width-50, height-50) # Inner
    
    # Corner decorations (simple curves)
    c.setStrokeColor(gold_color)
    c.setLineWidth(2)
    # Top Left
    c.arc(20, height-60, 60, height-20, 90, 90)
    # Top Right
    c.arc(width-60, height-60, width-20, height-20, 0, 90)
    # Bottom Left
    c.arc(20, 20, 60, 60, 180, 90)
    # Bottom Right
    c.arc(width-60, 20, width-20, 60, 270, 90)

    # 2. Blood Drop Icon with Cross
    # Draw centered at top
    cx, cy = width/2, height - 100
    c.setFillColor(red_color)
    c.setStrokeColor(red_color)
    p = c.beginPath()
    # Drop shape
    p.moveTo(cx, cy + 30)
    p.curveTo(cx + 25, cy, cx + 25, cy - 20, cx, cy - 40) # Right curve
    p.curveTo(cx - 25, cy - 20, cx - 25, cy, cx, cy + 30) # Left curve
    c.drawPath(p, fill=1, stroke=0)
    
    # White Cross
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.white)
    c.setLineWidth(4)
    c.line(cx, cy - 15, cx, cy + 5) # Vertical
    c.line(cx - 10, cy - 5, cx + 10, cy - 5) # Horizontal
    
    # 3. Header
    c.setFont("Times-Bold", 32)
    c.setFillColor(red_color)
    c.drawCentredString(width/2, height - 160, "BLOOD DONATION CERTIFICATE")
    
    # Decorative line below header
    c.setStrokeColor(gold_color)
    c.setLineWidth(1)
    c.line(100, height - 175, width - 100, height - 175)
    # Small center decoration on line
    c.circle(width/2, height - 175, 3, fill=1, stroke=0)

    # 4. Certify Text
    c.setFont("Times-Italic", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 220, "This is to proudly certify that")
    
    # 5. Donor Name
    c.setFont("Times-Bold", 28)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 270, donation['donor_name'].upper())
    # Underline name
    c.setStrokeColor(colors.Color(0.9, 0.8, 0.8)) # Faint red/pink
    c.line(150, height - 280, width - 150, height - 280)

    # 6. Body Text
    c.setFont("Times-Italic", 14)
    c.drawCentredString(width/2, height - 320, "has voluntarily donated blood and contributed to")
    c.drawCentredString(width/2, height - 340, "saving lives through the Blood Donor Management System.")
    
    # 7. Details Section
    # Draw lines for details
    start_y = height - 400
    line_height = 30
    left_margin = 180
    value_margin = 300
    
    c.setFont("Times-Bold", 14)
    c.setFillColor(colors.black)
    
    # Blood Group
    c.drawString(left_margin, start_y, "Blood Group:")
    c.drawString(value_margin, start_y, donation['blood_group'])
    c.setStrokeColor(colors.lightgrey)
    c.line(left_margin, start_y - 5, width - left_margin, start_y - 5)
    
    # Date
    c.drawString(left_margin, start_y - line_height, "Date of Donation:")
    c.drawString(value_margin, start_y - line_height, str(donation['donation_date']))
    c.line(left_margin, start_y - line_height - 5, width - left_margin, start_y - line_height - 5)



    # 8. Appreciation Text
    c.setFont("Times-Italic", 12)
    c.drawCentredString(width/2, height - 500, "Your selfless act of kindness and humanity is deeply appreciated.")
    c.drawCentredString(width/2, height - 520, "One donation can save up to three lives.")
    
    # 9. Hero Text
    c.setFont("Times-Italic", 16)
    c.setFillColor(colors.black)
    text = "Thank you for being a HERO"
    text_width = c.stringWidth(text, "Times-Italic", 16)
    start_x = (width - text_width) / 2
    c.drawString(start_x, height - 570, text)
    
    # Draw Heart next to text
    c.setFillColor(red_color)
    c.setStrokeColor(red_color)
    p = c.beginPath()
    hx, hy = start_x + text_width + 15, height - 565
    p.moveTo(hx, hy)
    p.curveTo(hx - 5, hy + 5, hx - 10, hy, hx, hy - 10)
    p.curveTo(hx + 10, hy, hx + 5, hy + 5, hx, hy)
    c.drawPath(p, fill=1, stroke=0)
    
    # Separator lines above footer
    c.setStrokeColor(colors.lightgrey)
    c.line(100, height - 600, 250, height - 600) # Left signature line
    c.line(width - 250, height - 600, width - 100, height - 600) # Right signature line

    # 10. Footer
    c.setFont("Times-Bold", 10)
    c.setFillColor(colors.black)
    
    c.drawString(100, height - 615, "Authorized By: Blood Bank Admin")
    c.drawRightString(width - 100, height - 615, "Organization: Life Saver Blood Network")
    


    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

def send_email_with_attachment(to_email, subject, body, attachment_bytes, filename):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to_email
    msg.set_content(body)

    msg.add_attachment(attachment_bytes, maintype='application', subtype='pdf', filename=filename)

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            if app.config['MAIL_USE_TLS']:
                server.starttls()
            if app.config['MAIL_USERNAME']:
                server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
    except ConnectionRefusedError:
        if app.config['MAIL_SERVER'] == 'localhost':
            # Fallback for dev mode: Write to file if server not running
            try:
                with open("sent_emails.txt", "a") as f:
                    f.write(f"--- MOCK EMAIL ---\nTo: {to_email}\nSubject: {subject}\nTime: {datetime.now()}\n\n{body}\n[Attachment: {filename} ({len(attachment_bytes)} bytes)]\n------------------\n\n")
            except:
                pass # If we can't write to file, just ignore
            print(f"Mock SMTP server unreachable. Email logged to sent_emails.txt")
        else:
            raise


if __name__ == '__main__':
    app.run(debug=True)
