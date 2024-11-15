import logging
import os
import sqlite3
from datetime import datetime
import shutil
from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user
from werkzeug.exceptions import HTTPException

def setup_logging():
    """Configure application logging"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'nfl_pickems.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create logger
    logger = logging.getLogger('nfl_pickems')
    return logger

def handle_error(e):
    """Global error handler for all exceptions"""
    if isinstance(e, HTTPException):
        response = {
            'error': True,
            'message': e.description,
            'status_code': e.code
        }
        return jsonify(response), e.code
    
    # Log the error
    current_app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    
    # Return error message
    response = {
        'error': True,
        'message': 'An unexpected error occurred'
    }
    return jsonify(response), 500

def require_admin(f):
    """Decorator to require admin access for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

class DatabaseManager:
    """Handle database backup and restore operations"""
    
    @classmethod
    def get_db_path(cls):
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        return db_uri.replace('sqlite:///', '')
    
    @classmethod
    def get_backup_dir(cls):
        backup_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'backups'
        )
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    @classmethod
    def create_backup(cls):
        """Create a backup of the database"""
        db_path = cls.get_db_path()
        backup_dir = cls.get_backup_dir()
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'nfl_pickems_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup
        shutil.copy2(db_path, backup_path)
        
        return backup_path
    
    @classmethod
    def restore_backup(cls, backup_path):
        """Restore database from a backup file"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Verify backup file
        cls._verify_backup(backup_path)
        
        # Restore database
        db_path = cls.get_db_path()
        shutil.copy2(backup_path, db_path)
    
    @classmethod
    def list_backups(cls):
        """List all available database backups"""
        backup_dir = cls.get_backup_dir()
        backups = []
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('nfl_pickems_backup_') and filename.endswith('.db'):
                backup_path = os.path.join(backup_dir, filename)
                backup_time = os.path.getmtime(backup_path)
                backup_size = os.path.getsize(backup_path)
                
                backups.append({
                    'filename': filename,
                    'path': backup_path,
                    'timestamp': datetime.fromtimestamp(backup_time).isoformat(),
                    'size': backup_size
                })
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    @classmethod
    def _verify_backup(cls, backup_path):
        """Verify that a backup file is a valid SQLite database"""
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Check if essential tables exist
            tables = ['user', 'game', 'pick']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    raise ValueError(f"Invalid backup: missing table '{table}'")
            
            conn.close()
        except sqlite3.Error as e:
            raise ValueError(f"Invalid SQLite database: {str(e)}")
