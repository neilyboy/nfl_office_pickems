import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_this_in_production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///../../data/nfl_pickems.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_PROTECTION = 'strong'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Remember me configuration
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Login configuration
    LOGIN_DISABLED = False
    USE_SESSION_FOR_NEXT = False
    
    # CORS configuration
    CORS_HEADERS = 'Content-Type'
    
    # Custom configuration
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes in seconds
