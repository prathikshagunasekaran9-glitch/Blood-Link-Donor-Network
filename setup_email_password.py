import re
import smtplib
import os

CONFIG_FILE = 'config.py'

def update_password():
    print("--- Update Email Password ---")
    print("Please enter the 16-character App Password generated from your Google Account.")
    print("(You can find this at https://myaccount.google.com/apppasswords)")
    new_password = input("Enter App Password (spaces will be removed automatically): ").strip().replace(" ", "")

    if len(new_password) == 0:
        print("Error: Password cannot be empty.")
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        # Regex to find the MAIL_PASSWORD line
        # Matches: MAIL_PASSWORD = '...' or "..."
        pattern = r"(MAIL_PASSWORD\s*=\s*)(['\"])(?:(?!(?<!\\)\2).)*\2"
        
        # Check if pattern exists
        if not re.search(pattern, content):
            print("Error: Could not find MAIL_PASSWORD setting in config.py")
            return

        # Replace with new password
        # Group 1 is "MAIL_PASSWORD = "
        # Group 2 is the quote type
        new_content = re.sub(pattern, f"\\1'{new_password}'", content)

        with open(CONFIG_FILE, 'w') as f:
            f.write(new_content)
        
        print(f"\nSuccess! Updated {CONFIG_FILE} with the new password.")
        
        # Verify
        verify_connection(new_password)

    except Exception as e:
        print(f"Error updating file: {e}")

def verify_connection(password):
    print("\n--- Verifying Connection ---")
    # Read other config values directly or use hardcoded check
    # We know the config is set to Gmail
    SERVER = 'smtp.gmail.com'
    PORT = 587
    USERNAME = 'prathikshagunasekaran9@gmail.com' # Extracted from context
    
    print(f"Connecting to {SERVER} as {USERNAME}...")
    try:
        with smtplib.SMTP(SERVER, PORT) as server:
            server.starttls()
            server.login(USERNAME, password)
            print("✅ LOGIN SUCCESSFUL! usage of App Password is correct.")
            print("You can now send certificates from the dashboard.")
    except smtplib.SMTPAuthenticationError:
        print("❌ Login Failed. The password was rejected.")
        print("Please ensure you generated an 'App Password' and not your regular login password.")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    update_password()
