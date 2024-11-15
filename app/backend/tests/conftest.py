import os
import sys
import pytest
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from flask_login import login_user, LoginManager
from flask import session

# Add the app directory to the Python path
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, app_path)

# Set test environment variables
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite://'  # Force in-memory database
os.environ['SECRET_KEY'] = 'test_secret_key'

# Import the app after setting environment variables
from app import app as flask_app, db, bcrypt
from app.models import User, Game, Pick

@pytest.fixture(scope='session', autouse=True)
def app_context():
    """Create an application context for the entire test session."""
    # Configure app for testing
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test_secret_key',
        'LOGIN_DISABLED': False,
        'SESSION_PROTECTION': 'strong',
        'PERMANENT_SESSION_LIFETIME': timedelta(minutes=30),
        'SESSION_COOKIE_SECURE': False,  # Allow non-HTTPS in testing
        'SESSION_COOKIE_HTTPONLY': True,
        'REMEMBER_COOKIE_SECURE': False,  # Allow non-HTTPS in testing
        'REMEMBER_COOKIE_HTTPONLY': True,
        'SESSION_TYPE': 'filesystem'  # Use filesystem session for testing
    })

    # Push an application context
    ctx = flask_app.app_context()
    ctx.push()

    # Initialize Flask-Login's test environment
    login_manager = LoginManager()
    login_manager.init_app(flask_app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = None
    login_manager.login_message = None

    # Create all database tables
    db.create_all()

    # Populate test data
    _populate_test_data()

    yield flask_app

    # Clean up
    db.session.remove()
    db.drop_all()
    ctx.pop()

@pytest.fixture(scope='function')
def app(app_context):
    """Set up a clean database for each test."""
    # Create tables
    db.create_all()
    
    # Clear any existing data
    db.session.query(Pick).delete()
    db.session.query(Game).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Add test data
    _populate_test_data()

    yield app_context

    # Clean up
    db.session.remove()
    db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    # Configure app for testing
    app.config.update({
        'LOGIN_DISABLED': False,
        'SESSION_PROTECTION': 'strong',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SESSION_COOKIE_SECURE': False,  # Allow non-HTTPS in testing
        'REMEMBER_COOKIE_SECURE': False,  # Allow non-HTTPS in testing
        'SESSION_COOKIE_HTTPONLY': True,
        'REMEMBER_COOKIE_HTTPONLY': True,
        'REMEMBER_COOKIE_DURATION': timedelta(days=1)
    })
    
    test_client = app.test_client()
    # Configure client to handle sessions
    test_client.environ_base = {
        'wsgi.url_scheme': 'http',  # Use HTTP for testing
        'REMOTE_ADDR': '127.0.0.1'
    }
    
    # Start with a clean session
    with test_client.session_transaction() as sess:
        sess.clear()
        # Ensure all session variables are cleared
        for key in list(sess.keys()):
            sess.pop(key)
        sess.modified = True
        # Ensure user is not authenticated
        if '_user_id' in sess:
            del sess['_user_id']
        if '_fresh' in sess:
            del sess['_fresh']
    
    yield test_client

@pytest.fixture
def authenticated_client(client, app):
    """A test client that is already authenticated."""
    # Get test user
    user = User.query.filter_by(username='testuser').first()
    
    # Set up session in test client
    with client.session_transaction() as sess:
        sess.clear()  # Start fresh
        sess['_user_id'] = str(user.id)  # Flask-Login expects string
        sess['_fresh'] = True
        sess.modified = True
    
    return client

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

def _populate_test_data():
    """Populate test data."""
    # Create test users
    admin = User(
        username='admin',
        email='admin@test.com',
        is_admin=True,
        first_login=False
    )
    admin.password = 'admin_password'
    db.session.add(admin)

    user = User(
        username='testuser',
        email='test@test.com',
        is_admin=False,
        first_login=False
    )
    user.password = 'test_password'
    db.session.add(user)

    try:
        db.session.commit()  # Commit users first to get their IDs
    except:
        db.session.rollback()
        raise

    # Create test games
    game1 = Game(
        espn_id='401547417',
        home_team='KC',
        away_team='DET',
        start_time=datetime.utcnow() + timedelta(days=1),
        week=1,
        season=2023,
        final_score_home=0,
        final_score_away=0,
        winner=None
    )
    db.session.add(game1)

    game2 = Game(
        espn_id='401547418',
        home_team='NYG',
        away_team='DAL',
        start_time=datetime.utcnow() - timedelta(hours=2),
        week=1,
        season=2023,
        final_score_home=0,
        final_score_away=0,
        winner=None,
        is_mnf=True
    )
    db.session.add(game2)

    try:
        db.session.commit()  # Commit games to get their IDs
    except:
        db.session.rollback()
        raise

    # Create test picks
    pick1 = Pick(
        user_id=user.id,
        game_id=game1.id,
        picked_team='KC',
        mnf_total_points=None,
        week=1
    )
    db.session.add(pick1)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise
