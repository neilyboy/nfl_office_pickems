import pytest
from flask import session
from app.models import User
from app import db

def test_login_success(client):
    """Test successful login."""
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'test_password'
    })
    assert response.status_code == 200
    assert response.json['success'] == True

def test_login_admin(client):
    """Test admin login."""
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'admin_password'
    })
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['is_admin'] == True

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'wrong_password'
    })
    assert response.status_code == 401
    assert response.json['success'] == False

def test_first_login_flag(client):
    """Test first login flag behavior."""
    # Create a new user with first_login=True
    user = User(
        username='newuser',
        email='new@test.com',
        first_login=True
    )
    user.password = 'test_password'
    db.session.add(user)
    db.session.commit()

    # Login with new user
    response = client.post('/api/login', json={
        'username': 'newuser',
        'password': 'test_password'
    })
    
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['first_login'] == True

def test_change_password(authenticated_client):
    """Test password change functionality."""
    response = authenticated_client.post('/api/change_password', json={
        'new_password': 'new_password'
    })
    
    assert response.status_code == 200
    assert response.json['success'] == True

def test_protected_route_access(authenticated_client):
    """Test that protected routes are accessible when authenticated."""
    response = authenticated_client.get('/api/picks?week=1')
    assert response.status_code == 200
    assert response.json['success'] == True

def test_protected_route_redirect(client):
    """Test that protected routes require authentication."""
    # Ensure we're not authenticated
    with client.session_transaction() as sess:
        sess.clear()
        # Ensure all session variables are cleared
        for key in list(sess.keys()):
            sess.pop(key)
        # Ensure user is not authenticated
        if '_user_id' in sess:
            del sess['_user_id']
        if '_fresh' in sess:
            del sess['_fresh']
        sess.modified = True
        print("Session after clear:", dict(sess))

    # Make request without authentication
    response = client.get('/api/picks?week=1', follow_redirects=True)
    print("Response status:", response.status_code)
    print("Response data:", response.json)
    assert response.status_code == 401  # Unauthorized
    assert response.json['success'] == False
    assert response.json['message'] == 'Authentication required'

def test_logout(authenticated_client):
    """Test logout functionality."""
    # First verify we can access a protected route
    response = authenticated_client.get('/api/picks?week=1')
    assert response.status_code == 200
    assert response.json['success'] == True

    # Logout
    authenticated_client.get('/api/logout')

    # Verify we can no longer access protected route
    response = authenticated_client.get('/api/picks?week=1')
    assert response.status_code == 401  # Unauthorized
    assert response.json['success'] == False
