from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime, timedelta
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
    
    # Initialize extensions with app
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
    
    # Import models
    from .models import User, Game, Pick
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import and register blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    
    def update_games():
        """Update game scores periodically"""
        with app.app_context():
            try:
                from .game_updater import update_game_scores
                update_game_scores()
            except Exception as e:
                logger.error(f"Error in scheduled update_games: {str(e)}")
    
    scheduler.add_job(update_games, 'interval', minutes=5, id='update_games')
    scheduler.start()
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=bcrypt.generate_password_hash('admin'),
                is_admin=True,
                first_login=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info('Created default admin user')
        
        # Add sample games if none exist
        if not Game.query.first():
            # Current week's games
            sample_games = [
                Game(
                    espn_id='401547959',
                    week=11,
                    season=2023,
                    home_team='BAL',
                    away_team='CIN',
                    start_time=datetime(2023, 11, 16, 20, 15),  # Thursday night game
                    is_mnf=False
                ),
                Game(
                    espn_id='401547960',
                    week=11,
                    season=2023,
                    home_team='CLE',
                    away_team='PIT',
                    start_time=datetime(2023, 11, 19, 13, 0),
                    is_mnf=False
                ),
                Game(
                    espn_id='401547961',
                    week=11,
                    season=2023,
                    home_team='GB',
                    away_team='LAC',
                    start_time=datetime(2023, 11, 19, 13, 0),
                    is_mnf=False
                ),
                Game(
                    espn_id='401547968',
                    week=11,
                    season=2023,
                    home_team='PHI',
                    away_team='KC',
                    start_time=datetime(2023, 11, 20, 20, 15),  # Monday night game
                    is_mnf=True
                )
            ]
            
            for game in sample_games:
                db.session.add(game)
            db.session.commit()
            logger.info('Added sample NFL games for week 11')
    
    return app

# For use by other modules
from .models import User, Game, Pick
