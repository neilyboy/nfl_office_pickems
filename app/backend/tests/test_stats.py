import pytest
import json
from app import db, User, Game, Pick
from datetime import datetime, timedelta

def test_leaderboard_overall(client):
    """Test overall leaderboard retrieval."""
    # Login first
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    data = json.loads(response.data)
    leaderboard = data['leaderboard']
    
    # Verify leaderboard structure
    assert len(leaderboard) > 0
    entry = leaderboard[0]
    assert 'username' in entry
    assert 'total_picks' in entry
    assert 'correct_picks' in entry
    assert 'accuracy' in entry
    
    # Verify sorting (highest correct picks first)
    for i in range(len(leaderboard) - 1):
        assert leaderboard[i]['correct_picks'] >= leaderboard[i + 1]['correct_picks']

def test_leaderboard_weekly(client):
    """Test weekly leaderboard retrieval."""
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    response = client.get('/api/leaderboard?week=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    leaderboard = data['leaderboard']
    
    # Verify week-specific data
    for entry in leaderboard:
        assert entry['total_picks'] <= 16  # Max games per week

def test_user_stats(client):
    """Test user statistics retrieval."""
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify weekly stats
    assert 'weekly_stats' in data
    weekly_stats = data['weekly_stats']
    for stat in weekly_stats:
        assert 'week' in stat
        assert 'total_picks' in stat
        assert 'correct_picks' in stat
        assert 'accuracy' in stat
        assert stat['accuracy'] >= 0 and stat['accuracy'] <= 100
    
    # Verify team stats
    assert 'team_stats' in data
    team_stats = data['team_stats']
    for stat in team_stats:
        assert 'team' in stat
        assert 'total_picks' in stat
        assert 'correct_picks' in stat
        assert 'accuracy' in stat
        assert stat['accuracy'] >= 0 and stat['accuracy'] <= 100

def test_other_user_stats_as_admin(client):
    """Test retrieving another user's stats as admin."""
    # Login as admin
    client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    
    # Get testuser's stats
    response = client.get('/api/stats?user_id=2')  # testuser's ID is 2
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'weekly_stats' in data
    assert 'team_stats' in data

def test_other_user_stats_as_regular_user(client):
    """Test that regular users cannot view others' stats."""
    # Login as regular user
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    # Try to get admin's stats
    response = client.get('/api/stats?user_id=1')  # admin's ID is 1
    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['success'] is False

def test_leaderboard_accuracy(client, app):
    """Test leaderboard accuracy calculation."""
    with app.app_context():
        # Add some more picks to verify accuracy calculation
        user = User.query.filter_by(username='testuser').first()
        game = Game.query.filter_by(espn_id='401547417').first()  # KC vs DET game
        
        # Add a correct pick
        pick = Pick(
            user_id=user.id,
            game_id=game.id,
            picked_team='DET',  # DET won this game
            week=1
        )
        db.session.add(pick)
        db.session.commit()
    
    # Get leaderboard
    client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password'
    })
    
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    data = json.loads(response.data)
    leaderboard = data['leaderboard']
    
    # Find testuser's entry
    user_entry = next(entry for entry in leaderboard if entry['username'] == 'testuser')
    assert user_entry['correct_picks'] > 0
    # Accuracy should be (correct_picks / total_picks) * 100
    expected_accuracy = (user_entry['correct_picks'] / user_entry['total_picks']) * 100
    assert abs(user_entry['accuracy'] - expected_accuracy) < 0.01  # Allow for floating-point imprecision
