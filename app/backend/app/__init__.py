from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import timedelta
import logging
from .config.logging_config import setup_logging

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_this_in_production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../../data/nfl_pickems.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_PROTECTION'] = 'strong'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['LOGIN_DISABLED'] = False
    app.config['USE_SESSION_FOR_NEXT'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app)
    migrate = Migrate(app, db)
    
    # Configure login manager
    login_manager.session_protection = 'strong'
    login_manager.needs_refresh_message = None
    login_manager.needs_refresh_message_category = None
    login_manager.refresh_view = None
    login_manager.login_view = None  # Disable redirect for unauthorized access
    login_manager.login_message = None  # Disable default login message

    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access attempts."""
        logger.warning('Unauthorized access attempt')
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        }), 401

    @login_manager.user_loader
    def load_user(user_id):
        """Load user from database."""
        try:
            if not user_id:
                return None
            from .models import User
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f'Error loading user {user_id}: {str(e)}')
            return None

    # Import models after db initialization
    from .models import User, Game, Pick
    
    # Initialize database manager
    from .utils import DatabaseManager
    db_manager = DatabaseManager(app)

    def update_games():
        """Update games from ESPN API."""
        try:
            from .espn_api import ESPNAPI
            espn_api = ESPNAPI()
            current_week = espn_api.get_current_week()
            games = espn_api.get_games(current_week)
            
            for game_data in games:
                game = Game.query.filter_by(espn_id=game_data['espn_id']).first()
                if not game:
                    game = Game(espn_id=game_data['espn_id'])
                    db.session.add(game)
                
                game.week = current_week
                game.home_team = game_data['home_team']
                game.away_team = game_data['away_team']
                game.start_time = game_data['start_time']
                
                if game_data['is_finished']:
                    game.final_score_home = game_data['home_score']
                    game.final_score_away = game_data['away_score']
                    game.winner = game_data['home_team'] if game_data['home_score'] > game_data['away_score'] else game_data['away_team']
            
            db.session.commit()
            logger.info(f"Successfully updated games for week {current_week}")
            
        except Exception as e:
            logger.error(f"Error updating games: {str(e)}")
            db.session.rollback()

    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_games, trigger="interval", minutes=10)
    scheduler.start()

    # Import and register blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
