import requests
from datetime import datetime, timedelta
import pytz
import time

class ESPNAPIError(Exception):
    """Custom exception for ESPN API errors"""
    pass

class ESPNAPI:
    BASE_URL = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl'
    RATE_LIMIT_DELAY = 1.0  # Delay between requests in seconds

    def __init__(self):
        self.last_request_time = 0
        self.headers = {
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '99'
        }

    def _make_request(self, url, params=None):
        """Make a rate-limited request to the ESPN API"""
        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last_request)
        
        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code != 200:
            raise ESPNAPIError(f"ESPN API request failed with status code {response.status_code}")
        
        self.last_request_time = time.time()
        return response.json()

    def get_current_week(self):
        """Get the current NFL week number"""
        try:
            data = self._make_request(f"{self.BASE_URL}/scoreboard")
            return data.get('week', {}).get('number', 1)
        except Exception as e:
            raise ESPNAPIError(f"Failed to get current week: {str(e)}")

    def _parse_game_data(self, data):
        """Parse ESPN API game data into our format"""
        games = []
        try:
            for event in data.get('events', []):
                competition = event['competitions'][0]
                home_team = competition['competitors'][0]
                away_team = competition['competitors'][1]
                
                # Convert ESPN's UTC time to datetime object
                start_time = datetime.strptime(
                    event['date'],
                    '%Y-%m-%dT%H:%MZ'
                ).replace(tzinfo=pytz.UTC)
                
                game_data = {
                    'espn_id': event['id'],
                    'week': data.get('week', {}).get('number', 1),
                    'home_team': home_team['team']['abbreviation'],
                    'away_team': away_team['team']['abbreviation'],
                    'start_time': start_time,
                    'home_score': int(home_team['score']) if home_team.get('score') else None,
                    'away_score': int(away_team['score']) if away_team.get('score') else None,
                    'is_finished': self._is_game_finished(competition)
                }
                
                games.append(game_data)
            
            return games
        except Exception as e:
            raise ESPNAPIError(f"Failed to parse game data: {str(e)}")

    def _is_game_finished(self, competition):
        """Check if a game is finished"""
        try:
            status = competition.get('status', {}).get('type', {})
            return status.get('completed', False)
        except Exception:
            return False

    def get_games(self, week):
        """Get all games for a specific week"""
        try:
            data = self._make_request(f"{self.BASE_URL}/scoreboard", params={'week': week})
            if not data:
                raise ESPNAPIError("Failed to fetch games: Empty response")
            return self._parse_game_data(data)
        except Exception as e:
            raise ESPNAPIError(f"Failed to fetch games: {str(e)}")

    def get_team_stats(self, team_abbr):
        """Get statistics for a specific team"""
        try:
            url = f"{self.BASE_URL}/teams/{team_abbr}/statistics"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise ESPNAPIError(f"Failed to fetch team stats: Status code {response.status_code}")
            
            data = response.json()
            if not data or 'stats' not in data:
                raise ESPNAPIError("Failed to fetch team stats: Invalid response format")
            
            return {stat['name']: stat['value'] for stat in data['stats']}
        except Exception as e:
            raise ESPNAPIError(f"Failed to fetch team stats: {str(e)}")

    def update_game_scores(self, week):
        """Update scores for games in a specific week"""
        try:
            games = self.get_games(week)
            return [game for game in games if game['is_finished']]
        except Exception as e:
            raise ESPNAPIError(f"Failed to update game scores for week {week}: {str(e)}")
