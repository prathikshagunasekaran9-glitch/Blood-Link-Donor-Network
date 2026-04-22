import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_very_secret'
    DATABASE = os.environ.get('DATABASE') or 'blood_donor.db'
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'blood_donor'

    # Email Config - MOCK LOCAL SERVER (Dev Mode)
    # MAIL_SERVER = 'localhost'
    # MAIL_PORT = 1025
    # MAIL_USERNAME = None
    # MAIL_PASSWORD = None
    # MAIL_USE_TLS = False
    # MAIL_DEFAULT_SENDER = 'noreply@bloodlink.com'
    
    # GMAIL SETTINGS (Uncomment to use Real Email)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'prathikshagunasekaran9@gmail.com'  
    MAIL_PASSWORD = 'femu ytwm neqk kxal' # App Password 
    MAIL_DEFAULT_SENDER = 'prathikshagunasekaran9@gmail.com' 

