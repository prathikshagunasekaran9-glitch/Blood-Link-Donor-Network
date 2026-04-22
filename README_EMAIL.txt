EMAIL SYSTEM INFORMATION
========================

Your BloodLink application is currently running in "Development Mode". 

In this mode, emails are NOT sent to the real internet to avoid spamming users or requiring sensitive passwords.
Instead, all emails are intercepted and saved to a file for verification.

WHERE ARE MY EMAILS?
--------------------
You can find all sent emails in the file:
   sent_emails.txt

(Located in the same folder as this file)

HOW TO VERIFY?
--------------
1. Open 'sent_emails.txt'
2. Scroll to the bottom to see the latest email.
3. You will see the To, From, Subject, and the content of the email.
4. The attachment content is also logged (as random looking characters).

HOW TO SEND REAL EMAILS?
------------------------
To send real emails, you must configure a real SMTP server (like Gmail, Outlook, or SendGrid).
Update the 'config.py' file with your credentials:

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'  (Not your login password!)
    MAIL_USE_TLS = True

WARNING: Be careful not to share your passwords!
