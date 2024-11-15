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
        with app.app_context():
            from .game_updater import update_game_scores
            update_game_scores()
    
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
    
    return app

# For use by other modules
from .models import User, Game, Pick
