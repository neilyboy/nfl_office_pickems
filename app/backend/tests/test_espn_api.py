import pytest
from unittest.mock import patch, MagicMock
from app.espn_api import ESPNAPI
from datetime import datetime

@pytest.fixture
def espn_api():
    return ESPNAPI()

@pytest.fixture
def mock_game_response():
    return {
        "events": [{
            "id": "401547417",
            "name": "Kansas City Chiefs at Detroit Lions",
            "date": "2023-09-08T00:20Z",
            "competitions": [{
                "competitors": [{
                    "homeAway": "home",
                    "team": {
                        "abbreviation": "DET",
                        "displayName": "Detroit Lions"
                    },
                    "score": "21"
                }, {
                    "homeAway": "away",
                    "team": {
                        "abbreviation": "KC",
                        "displayName": "Kansas City Chiefs"
                    },
                    "score": "20"
                }],
                "status": {
                    "type": {
                        "completed": True
                    }
                }
            }]
        }]
    }

def test_get_current_week():
    """Test getting current NFL week."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "week": {"number": 5}
        }
        mock_get.return_value.status_code = 200
        
        api = ESPNAPI()
        week = api.get_current_week()
        
        assert week == 5
        mock_get.assert_called_once()

def test_get_games(espn_api, mock_game_response):
    """Test getting games for a specific week."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_game_response
        mock_get.return_value.status_code = 200
        
        games = espn_api.get_games(week=1)
        
        assert len(games) == 1
        game = games[0]
        assert game['espn_id'] == '401547417'
        assert game['home_team'] == 'DET'
        assert game['away_team'] == 'KC'
        assert game['home_score'] == 21
        assert game['away_score'] == 20
        assert game['is_finished'] is True

def test_get_games_error_handling(espn_api):
    """Test error handling when getting games."""
    with patch('app.espn_api.requests.get') as mock_get:
        # Simulate API error
        mock_get.return_value.status_code = 500
        
        with pytest.raises(Exception) as exc_info:
            espn_api.get_games(week=1)
        
        assert "Failed to fetch games" in str(exc_info.value)

def test_parse_game_data(espn_api, mock_game_response):
    """Test parsing raw game data."""
    games = espn_api._parse_game_data(mock_game_response)
    
    assert len(games) == 1
    game = games[0]
    assert game['espn_id'] == '401547417'
    assert game['home_team'] == 'DET'
    assert game['away_team'] == 'KC'
    assert game['home_score'] == 21
    assert game['away_score'] == 20
    assert game['is_finished'] is True
    assert isinstance(game['start_time'], datetime)

def test_get_team_stats():
    """Test getting team statistics."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "stats": [{
                "name": "Total Offense",
                "value": 400.5
            }, {
                "name": "Points Per Game",
                "value": 28.3
            }]
        }
        mock_get.return_value.status_code = 200
        
        api = ESPNAPI()
        stats = api.get_team_stats("KC")
        
        assert len(stats) > 0
        assert isinstance(stats, dict)
        assert stats["Total Offense"] == 400.5
        assert stats["Points Per Game"] == 28.3

def test_get_team_stats_error():
    """Test error handling for team statistics."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        
        api = ESPNAPI()
        with pytest.raises(Exception) as exc_info:
            api.get_team_stats("INVALID")
        
        assert "Failed to fetch team stats" in str(exc_info.value)

def test_update_game_scores(espn_api, mock_game_response):
    """Test updating game scores."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_game_response
        mock_get.return_value.status_code = 200
        
        updated_games = espn_api.update_game_scores(week=1)
        
        assert len(updated_games) == 1
        game = updated_games[0]
        assert game['home_score'] == 21
        assert game['away_score'] == 20
        assert game['is_finished'] is True

def test_game_status_parsing(espn_api):
    """Test parsing different game statuses."""
    test_cases = [
        ({
            "status": {
                "type": {
                    "completed": True
                }
            }
        }, True),
        ({
            "status": {
                "type": {
                    "completed": False
                }
            }
        }, False),
        ({
            "status": {
                "type": {
                    "completed": False,
                    "detail": "Postponed"
                }
            }
        }, False)
    ]
    
    for competition, expected_status in test_cases:
        is_finished = espn_api._is_game_finished(competition)
        assert is_finished == expected_status

def test_rate_limiting():
    """Test API rate limiting functionality."""
    with patch('app.espn_api.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"week": {"number": 1}}
        mock_get.return_value.status_code = 200
        
        api = ESPNAPI()
        
        # Make multiple rapid requests
        for _ in range(5):
            api.get_current_week()
        
        # Verify rate limiting headers are respected
        assert mock_get.call_count == 5
        for call in mock_get.call_args_list:
            headers = call.kwargs.get('headers', {})
            assert 'X-RateLimit-Limit' in headers
