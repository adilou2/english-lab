import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///english_lab.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.5-flash-lite'
    
    # Debug: print API key status
    print(f"GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")
    if GEMINI_API_KEY:
        print(f"GEMINI_API_KEY length: {len(GEMINI_API_KEY)}")
