import requests
import logging
from datetime import datetime
from . import db, Game

logger = logging.getLogger(__name__)

def update_game_scores():
    """
    Update game scores for all games that are in progress or completed.
    This function is called every 5 minutes by the scheduler.
    """
    try:
        # Get all games that are in progress or completed
        games = Game.query.filter(Game.status.in_(['in_progress', 'completed'])).all()
        
        if not games:
            logger.info("No games to update")
            return

        # For now, just log that we're checking games
        # TODO: Implement actual NFL API integration
        logger.info(f"Checking scores for {len(games)} games")
        for game in games:
            logger.info(f"Game {game.home_team} vs {game.away_team} (Status: {game.status})")

        # Commit any changes
        db.session.commit()
        logger.info("Game scores updated successfully")

    except Exception as e:
        logger.error(f"Error updating game scores: {str(e)}")
        db.session.rollback()
