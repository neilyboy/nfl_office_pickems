import pytest
import json
from datetime import datetime, timedelta
from app import db, Game, Pick

def test_get_picks(client):
    """Test retrieving user picks."""
    # Login first
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Get picks for week 1
    response = client.get('/api/picks?week=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    picks = data['picks']
    assert len(picks) == 2
    assert any(p['picked_team'] == 'KC' for p in picks)
    assert any(p['picked_team'] == 'BUF' for p in picks)

def test_submit_picks(client):
    """Test submitting new picks."""
    # Login first
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Submit picks for week 1
    response = client.post('/api/picks', json={
        'week': 1,
        'picks': [
            {'game_id': 1, 'team': 'DET'},
            {'game_id': 2, 'team': 'NYJ', 'mnf_total_points': 42}
        ]
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify picks were updated
    response = client.get('/api/picks?week=1')
    data = json.loads(response.data)
    picks = data['picks']
    assert any(p['picked_team'] == 'DET' for p in picks)
    assert any(p['picked_team'] == 'NYJ' for p in picks)

def test_pick_locking(client, app):
    """Test that picks are locked before game start."""
    with app.app_context():
        # Update game start time to be very soon
        game = Game.query.get(1)
        game.start_time = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
    
    # Login as regular user
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Try to submit picks
    response = client.post('/api/picks', json={
        'week': 1,
        'picks': [
            {'game_id': 1, 'team': 'DET'}
        ]
    })
    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'locked' in data['message'].lower()

def test_admin_override_lock(client, app):
    """Test that admins can override pick locking."""
    with app.app_context():
        # Update game start time to be very soon
        game = Game.query.get(1)
        game.start_time = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
    
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Submit picks as admin
    response = client.post('/api/picks', json={
        'week': 1,
        'picks': [
            {'game_id': 1, 'team': 'DET'}
        ]
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

def test_mnf_points_required(client):
    """Test that MNF total points are required for Monday night games."""
    # Login first
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Try to submit MNF pick without points
    response = client.post('/api/picks', json={
        'week': 1,
        'picks': [
            {'game_id': 2, 'team': 'NYJ'}  # Game 2 is MNF
        ]
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'points' in data['message'].lower()
