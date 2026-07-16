import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration - handle Render's PostgreSQL URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///english_lab.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.5-flash-lite'
    
    # Debug: print API key status
    print(f"GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")
    if GEMINI_API_KEY:
        print(f"GEMINI_API_KEY length: {len(GEMINI_API_KEY)}")
