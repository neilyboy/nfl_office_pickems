import requests
import logging
from datetime import datetime
from .models import Game
from . import db

logger = logging.getLogger(__name__)

def get_espn_game_data(game_id):
    """
    Fetch game data from ESPN's API for a specific game.
    """
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard/{game_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching ESPN data for game {game_id}: {str(e)}")
        return None

def parse_game_status(espn_data):
    """
    Parse game status from ESPN data.
    Returns: (status, home_score, away_score, winner)
    """
    try:
        if not espn_data or 'status' not in espn_data:
            return None, None, None, None

        status_type = espn_data['status']['type']
        if status_type['completed']:
            game_status = 'completed'
        elif status_type['state'] == 'in':
            game_status = 'in_progress'
        else:
            game_status = 'scheduled'

        # Get scores if available
        home_score = None
        away_score = None
        winner = None

        if 'competitions' in espn_data and espn_data['competitions']:
            competition = espn_data['competitions'][0]
            if 'competitors' in competition:
                for team in competition['competitors']:
                    score = int(team.get('score', 0))
                    if team['homeAway'] == 'home':
                        home_score = score
                    else:
                        away_score = score

                # Determine winner if game is completed
                if game_status == 'completed' and home_score is not None and away_score is not None:
                    winner = competition['competitors'][0]['team']['abbreviation'] if home_score > away_score else competition['competitors'][1]['team']['abbreviation']

        return game_status, home_score, away_score, winner
    except Exception as e:
        logger.error(f"Error parsing ESPN data: {str(e)}")
        return None, None, None, None

def update_game_scores():
    """
    Update game scores for all games that are in progress or completed.
    This function is called every 5 minutes by the scheduler.
    """
    try:
        # Get all games that haven't been completed yet
        games = Game.query.filter(
            Game.status.in_(['scheduled', 'in_progress'])
        ).all()
        
        if not games:
            logger.info("No active games to update")
            return

        logger.info(f"Checking scores for {len(games)} games")
        current_time = datetime.utcnow()
        updates_made = False
        
        for game in games:
            # Update game status based on start time
            if game.status == 'scheduled' and current_time >= game.start_time:
                game.status = 'in_progress'
                updates_made = True
                logger.info(f"Game {game.home_team} vs {game.away_team} is now in progress")
            
            # Fetch and update game data from ESPN
            espn_data = get_espn_game_data(game.espn_id)
            if espn_data:
                status, home_score, away_score, winner = parse_game_status(espn_data)
                
                if status and status != game.status:
                    game.status = status
                    updates_made = True
                
                if home_score is not None and away_score is not None:
                    if game.final_score_home != home_score or game.final_score_away != away_score:
                        game.final_score_home = home_score
                        game.final_score_away = away_score
                        updates_made = True
                        logger.info(f"Updated scores for {game.home_team} vs {game.away_team}: {home_score}-{away_score}")
                
                if winner and game.winner != winner:
                    game.winner = winner
                    updates_made = True
                    logger.info(f"Game completed: {game.home_team} vs {game.away_team}, Winner: {winner}")

        # Only commit if we made changes
        if updates_made:
            db.session.commit()
            logger.info("Game updates committed successfully")
        else:
            logger.info("No updates needed for active games")

    except Exception as e:
        logger.error(f"Error updating game scores: {str(e)}")
        db.session.rollback()
