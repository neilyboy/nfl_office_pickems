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
    """Decorator to require admin privileges for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({
                'error': True,
                'message': 'Admin privileges required',
                'status_code': 403
            }), 403
        return f(*args, **kwargs)
    return decorated_function

class DatabaseManager:
    """Handle database backup and restore operations"""
    
    def __init__(self, app):
        self.app = app
        self.db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        self.backup_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'backups'
        )
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """Create a backup of the database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}.db')
        
        try:
            # Create a copy of the database file
            shutil.copy2(self.db_path, backup_path)
            
            # Verify the backup
            self._verify_backup(backup_path)
            
            self.app.logger.info(f"Database backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            self.app.logger.error(f"Failed to create database backup: {str(e)}")
            raise
    
    def restore_backup(self, backup_path):
        """Restore database from a backup file"""
        try:
            # Verify the backup before restoring
            self._verify_backup(backup_path)
            
            # Create a temporary backup of the current database
            temp_backup = self.create_backup()
            
            try:
                # Replace the current database with the backup
                shutil.copy2(backup_path, self.db_path)
                self.app.logger.info(f"Database restored successfully from: {backup_path}")
            except Exception as e:
                # If restore fails, try to recover the original database
                shutil.copy2(temp_backup, self.db_path)
                raise Exception(f"Failed to restore database: {str(e)}")
            
        except Exception as e:
            self.app.logger.error(f"Database restore failed: {str(e)}")
            raise
    
    def list_backups(self):
        """List all available database backups"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_') and filename.endswith('.db'):
                filepath = os.path.join(self.backup_dir, filename)
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath))
                })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def _verify_backup(self, backup_path):
        """Verify that a backup file is a valid SQLite database"""
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            if not tables:
                raise Exception("Backup verification failed: No tables found in database")
            
            return True
        except sqlite3.Error as e:
            raise Exception(f"Backup verification failed: {str(e)}")
