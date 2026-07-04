import os
from dotenv import load_dotenv

# Base directory path of this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load configuration from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    """Base configuration class containing application settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-fallback-key-should-be-changed'
    
    # Store SQLite database in /tmp on Vercel (read-only filesystem workaround) or local 'instance' folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'sqlite:////tmp/notes.db' if os.environ.get('VERCEL') == '1' else
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'notes.db')
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API credentials for AI Generative services
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL') or 'gemini-2.0-flash'
