import pytest
import json
import os
import sqlite3
from app import db, User, Game, Pick

def test_create_backup(client):
    """Test creating a database backup."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Create backup
    response = client.post('/api/admin/backup')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'backup_path' in data
    
    # Verify backup file exists and is a valid SQLite database
    backup_path = data['backup_path']
    assert os.path.exists(backup_path)
    
    # Try opening the backup file as SQLite database
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()
    
    # Check if essential tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert 'user' in tables
    assert 'game' in tables
    assert 'pick' in tables
    
    conn.close()

def test_list_backups(client):
    """Test listing available backups."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # First create a backup
    client.post('/api/admin/backup')
    
    # List backups
    response = client.get('/api/admin/backups')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'backups' in data
    backups = data['backups']
    assert len(backups) > 0
    
    # Verify backup entry structure
    backup = backups[0]
    assert 'filename' in backup
    assert 'path' in backup
    assert 'created_at' in backup
    assert 'size' in backup
    assert backup['size'] > 0

def test_restore_backup(client, app):
    """Test restoring from a backup."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Create initial backup
    response = client.post('/api/admin/backup')
    backup_path = json.loads(response.data)['backup_path']
    
    # Make some changes to the database
    with app.app_context():
        new_user = User(
            username='tempuser',
            password_hash='temp',
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
    
    # Restore from backup
    response = client.post('/api/admin/restore', json={
        'backup_path': backup_path
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify the changes were reverted
    with app.app_context():
        assert User.query.filter_by(username='tempuser').first() is None

def test_backup_as_regular_user(client):
    """Test that regular users cannot access backup functionality."""
    # Login as regular user
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Try to create backup
    response = client.post('/api/admin/backup')
    assert response.status_code == 403
    
    # Try to list backups
    response = client.get('/api/admin/backups')
    assert response.status_code == 403
    
    # Try to restore backup
    response = client.post('/api/admin/restore', json={
        'backup_path': 'some/path'
    })
    assert response.status_code == 403

def test_restore_invalid_backup(client):
    """Test restoring from an invalid backup file."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Try to restore from non-existent file
    response = client.post('/api/admin/restore', json={
        'backup_path': 'nonexistent/backup.db'
    })
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data['message'].lower()

def test_backup_verification(client, tmp_path):
    """Test backup file verification."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Create an invalid backup file
    invalid_backup = tmp_path / "invalid_backup.db"
    invalid_backup.write_text("This is not a SQLite database")
    
    # Try to restore from invalid file
    response = client.post('/api/admin/restore', json={
        'backup_path': str(invalid_backup)
    })
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'invalid' in data['message'].lower()
