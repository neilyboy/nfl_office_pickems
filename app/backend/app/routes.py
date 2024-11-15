from flask import Blueprint, jsonify, request, send_file, current_app
from flask_login import current_user, login_user, logout_user
from . import db, bcrypt, User, Game, Pick, login_manager
from datetime import datetime, timedelta
import json
from sqlalchemy import case, func, distinct
from .utils import require_admin, DatabaseManager
from functools import wraps
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

bp = Blueprint('main', __name__)

@bp.route('/api/login', methods=['POST'])
def login():
    if not request.is_json:
        logger.warning('Login attempt with non-JSON data')
        return jsonify({
            'success': False,
            'message': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logger.warning(f'Login attempt with missing credentials: username={bool(username)}, password={bool(password)}')
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        }), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        logger.info(f'Successful login for user: {user.username}')
        return jsonify({
            'success': True,
            'is_admin': user.is_admin,
            'first_login': user.first_login
        })
    else:
        logger.warning(f'Failed login attempt for username: {username}')
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401

@bp.route('/api/change_password', methods=['POST'])
@auth_required
def change_password():
    data = request.get_json()
    current_user.password_hash = bcrypt.generate_password_hash(data['new_password'])
    current_user.first_login = False
    db.session.commit()
    logger.info(f'Password changed for user: {current_user.username}')
    return jsonify({'success': True})

@bp.route('/api/picks', methods=['GET', 'POST'])
@auth_required
def picks():
    """Handle picks for the current user."""
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'week' not in data:
            logger.warning('Picks submission with missing week parameter')
            return jsonify({'success': False, 'message': 'Week parameter is required'}), 400
            
        # Process picks submission
        week = data['week']
        picks_data = data.get('picks', [])
        
        # Validate week
        if not isinstance(week, int) or week < 1 or week > 18:
            logger.warning(f'Picks submission with invalid week: {week}')
            return jsonify({'success': False, 'message': 'Invalid week'}), 400
        
        # Delete existing picks for this week
        Pick.query.filter_by(user_id=current_user.id, week=week).delete()
        
        # Add new picks
        for pick in picks_data:
            new_pick = Pick(
                user_id=current_user.id,
                week=week,
                game_id=pick['game_id'],
                picked_team=pick['picked_team'],
                mnf_total_points=pick.get('mnf_total_points')
            )
            db.session.add(new_pick)
        
        try:
            db.session.commit()
            logger.info(f'Picks submitted for user: {current_user.username}, week: {week}')
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error submitting picks for user: {current_user.username}, week: {week}, error: {str(e)}')
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        # GET request - return picks for the specified week
        week = request.args.get('week', type=int)
        if not week:
            logger.warning('Picks request with missing week parameter')
            return jsonify({
                'success': False,
                'message': 'Week parameter is required'
            }), 400

        picks = Pick.query.filter_by(user_id=current_user.id, week=week).all()
        picks_list = []
        for pick in picks:
            picks_list.append({
                'id': pick.id,
                'user_id': pick.user_id,
                'week': pick.week,
                'game_id': pick.game_id,
                'picked_team': pick.picked_team,
                'mnf_total_points': pick.mnf_total_points
            })

        logger.info(f'Picks retrieved for user: {current_user.username}, week: {week}')
        return jsonify({
            'success': True,
            'picks': picks_list
        })

@bp.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@auth_required
@require_admin
def manage_users():
    if request.method == 'GET':
        users = User.query.all()
        logger.info(f'Users retrieved for admin: {current_user.username}')
        return jsonify({
            'users': [{
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            } for user in users]
        })

    if request.method == 'POST':
        data = request.get_json()
        new_user = User(
            username=data['username'],
            password_hash=bcrypt.generate_password_hash('password'),
            is_admin=data.get('is_admin', False)
        )
        db.session.add(new_user)
        db.session.commit()
        logger.info(f'New user created by admin: {current_user.username}, user: {new_user.username}')
        return jsonify({'success': True, 'id': new_user.id})

    if request.method == 'PUT':
        data = request.get_json()
        user = User.query.get(data['id'])
        if not user:
            logger.warning(f'User update attempt for non-existent user: {data["id"]}')
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if 'username' in data:
            user.username = data['username']
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'password' in data:
            user.password_hash = bcrypt.generate_password_hash(data['password'])
            user.first_login = True
        
        db.session.commit()
        logger.info(f'User updated by admin: {current_user.username}, user: {user.username}')
        return jsonify({'success': True})

    if request.method == 'DELETE':
        user = User.query.get(request.args.get('id', type=int))
        if not user:
            logger.warning(f'User deletion attempt for non-existent user: {request.args.get("id", type=int)}')
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        logger.info(f'User deleted by admin: {current_user.username}, user: {user.username}')
        return jsonify({'success': True})

@bp.route('/api/admin/backup', methods=['POST'])
@auth_required
@require_admin
def create_backup():
    try:
        backup_path = DatabaseManager.create_backup()
        logger.info(f'Backup created by admin: {current_user.username}, path: {backup_path}')
        return jsonify({
            'success': True,
            'backup_path': backup_path
        })
    except Exception as e:
        logger.error(f'Error creating backup for admin: {current_user.username}, error: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/api/admin/backup/restore', methods=['POST'])
@auth_required
@require_admin
def restore_backup():
    data = request.get_json()
    backup_path = data.get('backup_path')
    
    if not backup_path:
        logger.warning(f'Backup restore attempt with missing path by admin: {current_user.username}')
        return jsonify({
            'success': False,
            'message': 'Backup path not provided'
        }), 400
    
    try:
        DatabaseManager.restore_backup(backup_path)
        logger.info(f'Backup restored by admin: {current_user.username}, path: {backup_path}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error restoring backup for admin: {current_user.username}, error: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/api/admin/backups', methods=['GET'])
@auth_required
@require_admin
def list_backups():
    try:
        backups = DatabaseManager.list_backups()
        logger.info(f'Backups listed by admin: {current_user.username}')
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        logger.error(f'Error listing backups for admin: {current_user.username}, error: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/api/leaderboard', methods=['GET'])
@auth_required
def leaderboard():
    """Legacy endpoint - redirects to season leaderboard"""
    return season_leaderboard()

@bp.route('/api/leaderboard/season', methods=['GET'])
@auth_required
def season_leaderboard():
    try:
        # Get all picks for the season
        picks_query = db.session.query(
            Pick.user_id,
            func.count(case([(Pick.picked_team == Game.winner, 1)])).label('correct_picks'),
            func.count(Pick.id).label('total_picks'),
            func.count(distinct(Pick.week)).label('weeks_played')
        ).join(Game)
        
        picks_query = picks_query.group_by(Pick.user_id)
        picks_results = picks_query.all()
        
        # Calculate accuracy and create leaderboard
        leaderboard = []
        for user_id, correct_picks, total_picks, weeks_played in picks_results:
            user = User.query.get(user_id)
            accuracy = (correct_picks / total_picks * 100) if total_picks > 0 else 0
            leaderboard.append({
                'id': user.id,
                'username': user.username,
                'correct': correct_picks,
                'total': total_picks,
                'weekly_wins': 0,  # TODO: Implement weekly wins calculation
                'streak': 0,  # TODO: Implement streak calculation
                'accuracy': round(accuracy, 2)
            })
        
        # Sort by correct picks (descending) and username (ascending)
        leaderboard.sort(key=lambda x: (-x['correct'], x['username']))
        
        logger.info(f'Season leaderboard retrieved for user: {current_user.username}')
        return jsonify(leaderboard)
    except Exception as e:
        logger.error(f'Error retrieving season leaderboard: {str(e)}')
        return jsonify([])

@bp.route('/api/leaderboard/weekly', methods=['GET'])
@auth_required
def weekly_leaderboard():
    try:
        week = request.args.get('week', type=int)
        if week is None:
            return jsonify([])
        
        # Get all picks for the specified week
        picks_query = db.session.query(
            Pick.user_id,
            func.count(case([(Pick.picked_team == Game.winner, 1)])).label('correct_picks'),
            func.count(Pick.id).label('total_picks')
        ).join(Game).filter(Pick.week == week)
        
        picks_query = picks_query.group_by(Pick.user_id)
        picks_results = picks_query.all()
        
        # Calculate accuracy and create leaderboard
        leaderboard = []
        for user_id, correct_picks, total_picks in picks_results:
            user = User.query.get(user_id)
            accuracy = (correct_picks / total_picks * 100) if total_picks > 0 else 0
            leaderboard.append({
                'id': user.id,
                'username': user.username,
                'correct': correct_picks,
                'total': total_picks,
                'accuracy': round(accuracy, 2)
            })
        
        # Sort by correct picks (descending) and username (ascending)
        leaderboard.sort(key=lambda x: (-x['correct'], x['username']))
        
        logger.info(f'Weekly leaderboard retrieved for week {week} by user: {current_user.username}')
        return jsonify(leaderboard)
    except Exception as e:
        logger.error(f'Error retrieving weekly leaderboard: {str(e)}')
        return jsonify([])

@bp.route('/api/stats', methods=['GET'])
@auth_required
def get_user_stats():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401

    # Get all picks for the current user
    picks = Pick.query.filter_by(user_id=current_user.id).all()
    
    if not picks:
        return jsonify({
            'total_correct': 0,
            'accuracy': 0,
            'best_week': None,
            'current_streak': 0,
            'weekly_stats': []
        })

    # Group picks by week
    picks_by_week = {}
    for pick in picks:
        week = pick.week
        if week not in picks_by_week:
            picks_by_week[week] = {'correct': 0, 'total': 0}
        
        picks_by_week[week]['total'] += 1
        if pick.picked_team == Game.winner:
            picks_by_week[week]['correct'] += 1

    # Calculate weekly stats
    weekly_stats = []
    total_correct = 0
    total_picks = 0
    best_week = {'week': None, 'correct': 0}
    
    for week, stats in picks_by_week.items():
        correct = stats['correct']
        total = stats['total']
        accuracy = (correct / total * 100) if total > 0 else 0
        
        weekly_stats.append({
            'week': week,
            'correct': correct,
            'total': total,
            'accuracy': accuracy
        })
        
        total_correct += correct
        total_picks += total
        
        if correct > best_week['correct']:
            best_week = {'week': week, 'correct': correct}

    # Calculate current streak
    current_streak = 0
    recent_picks = Pick.query.join(Game).filter(
        Pick.user_id == current_user.id,
        Game.has_ended == True
    ).order_by(Game.start_time.desc()).all()

    for pick in recent_picks:
        if pick.picked_team == Game.winner:
            current_streak += 1
        else:
            break

    # Sort weekly stats by week number
    weekly_stats.sort(key=lambda x: x['week'])

    return jsonify({
        'total_correct': total_correct,
        'accuracy': (total_correct / total_picks * 100) if total_picks > 0 else 0,
        'best_week': best_week,
        'current_streak': current_streak,
        'weekly_stats': weekly_stats
    })

@bp.route('/api/get_picks')
@auth_required
def get_picks():
    """Get picks for a specific week."""
    week = request.args.get('week', type=int)
    if not week:
        logger.warning('Picks request with missing week parameter')
        return jsonify({
            'success': False,
            'message': 'Week parameter is required'
        }), 400

    picks = Pick.query.filter_by(week=week).all()
    picks_list = []
    for pick in picks:
        picks_list.append({
            'id': pick.id,
            'user_id': pick.user_id,
            'week': pick.week,
            'game_id': pick.game_id,
            'team_id': pick.team_id,
            'points': pick.points,
            'result': pick.result
        })

    logger.info(f'Picks retrieved for user: {current_user.username}')
    return jsonify({
        'success': True,
        'picks': picks_list
    })

@bp.route('/api/logout')
@auth_required
def logout():
    """Handle user logout."""
    logger.info(f'User logged out: {current_user.username}')
    logout_user()
    return jsonify({'success': True})

@bp.route('/api/games/week/<int:week>')
@auth_required
def get_games_for_week(week):
    try:
        # Get current NFL season
        current_year = datetime.now().year
        # If we're in Jan-July, we're looking at the previous season
        current_season = current_year - 1 if datetime.now().month < 8 else current_year
        
        logger.info(f"Fetching games for week {week} of {current_season} season")
        
        games = Game.query.filter_by(week=week, season=current_season).all()
        logger.info(f"Found {len(games)} existing games in database")
        
        if not games:
            # Try to fetch games from ESPN API
            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
                params = {
                    'limit': 100,
                    'dates': current_season,
                    'week': str(week),
                    'seasontype': 2  # Regular season
                }
                logger.info(f"Fetching games from ESPN API: {url} with params {params}")
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"ESPN API Response: {data}")
                
                if 'events' in data:
                    logger.info(f"Found {len(data['events'])} games from ESPN API")
                    for event in data['events']:
                        # Skip if game already exists
                        if Game.query.filter_by(espn_id=event['id']).first():
                            logger.info(f"Game {event['id']} already exists, skipping")
                            continue
                            
                        competition = event['competitions'][0]
                        home_team = None
                        away_team = None
                        
                        for team in competition['competitors']:
                            if team['homeAway'] == 'home':
                                home_team = team['team']['abbreviation']
                            else:
                                away_team = team['team']['abbreviation']
                        
                        if home_team and away_team:
                            start_time = datetime.strptime(competition['date'], "%Y-%m-%dT%H:%M:%SZ")
                            new_game = Game(
                                espn_id=event['id'],
                                week=week,
                                season=current_season,
                                home_team=home_team,
                                away_team=away_team,
                                start_time=start_time,
                                status='scheduled'
                            )
                            db.session.add(new_game)
                            logger.info(f"Added new game: {home_team} vs {away_team}")
                    
                    db.session.commit()
                    logger.info("Successfully saved new games to database")
                    # Fetch games again after adding new ones
                    games = Game.query.filter_by(week=week, season=current_season).all()
                else:
                    logger.warning("No events found in ESPN API response")
            
            except Exception as e:
                logger.error(f"Error fetching games from ESPN API: {str(e)}")
                logger.exception(e)
        
        game_data = [{
            'id': game.id,
            'espn_id': game.espn_id,
            'week': game.week,
            'season': game.season,
            'home_team': game.home_team,
            'away_team': game.away_team,
            'start_time': game.start_time.isoformat(),
            'is_mnf': game.is_mnf,
            'final_score_home': game.final_score_home,
            'final_score_away': game.final_score_away,
            'winner': game.winner,
            'status': game.status
        } for game in games]
        
        logger.info(f"Returning {len(game_data)} games")
        return jsonify(game_data)
    
    except Exception as e:
        logger.error(f"Error getting games for week {week}: {str(e)}")
        logger.exception(e)
        return jsonify({'error': str(e)}), 500
