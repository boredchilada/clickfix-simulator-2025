import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'changeme_please'
    SERVER_URL = os.environ.get('SERVER_NAME') or '127.0.0.1:443'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///training_log.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Customization
    PAYLOAD_MESSAGE = os.environ.get('PAYLOAD_MESSAGE') or 'This was a ClickFix security training exercise. In a real attack, your system would now be compromised. Please review the training material.'
    TRAINING_URL = os.environ.get('TRAINING_URL') or '/training'
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

    # Stealth Configuration
    # These endpoints can be renamed to blend in with target environment traffic
    ENDPOINT_PAYLOAD = os.environ.get('ENDPOINT_PAYLOAD') or '/api/v2/config'
    ENDPOINT_VERIFY = os.environ.get('ENDPOINT_VERIFY') or '/verify'
    ENDPOINT_TRACK = os.environ.get('ENDPOINT_TRACK') or '/track/click'