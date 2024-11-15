from flask import jsonify, request, send_file
from flask_login import current_user, login_user, logout_user, login_manager
from app import app, db, bcrypt, User, Game, Pick, login_manager
from datetime import datetime, timedelta
import json
from sqlalchemy import case, func
from app.utils import require_admin
from app import db_manager
from functools import wraps
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated using Flask-Login's current_user
        if not current_user.is_authenticated:
            logger.warning('Authentication required')
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
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

@app.route('/api/change_password', methods=['POST'])
@auth_required
def change_password():
    data = request.get_json()
    current_user.password_hash = bcrypt.generate_password_hash(data['new_password'])
    current_user.first_login = False
    db.session.commit()
    logger.info(f'Password changed for user: {current_user.username}')
    return jsonify({'success': True})

@app.route('/api/picks', methods=['GET', 'POST'])
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

@app.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
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

@app.route('/api/admin/backup', methods=['POST'])
@auth_required
@require_admin
def create_backup():
    try:
        backup_path = db_manager.create_backup()
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

@app.route('/api/admin/backup/restore', methods=['POST'])
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
        db_manager.restore_backup(backup_path)
        logger.info(f'Backup restored by admin: {current_user.username}, path: {backup_path}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error restoring backup for admin: {current_user.username}, error: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/backups', methods=['GET'])
@auth_required
@require_admin
def list_backups():
    try:
        backups = db_manager.list_backups()
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

@app.route('/api/leaderboard', methods=['GET'])
@auth_required
def leaderboard():
    week = request.args.get('week', type=int)
    
    # Get all picks for the week
    picks_query = db.session.query(
        Pick.user_id,
        func.count(case([(Pick.picked_team == Game.winner, 1)])).label('correct_picks'),
        func.count(Pick.id).label('total_picks')
    ).join(Game).filter(Pick.week == week)
    
    if week is None:
        picks_query = picks_query.group_by(Pick.user_id)
    else:
        picks_query = picks_query.filter(Pick.week == week).group_by(Pick.user_id)
    
    picks_results = picks_query.all()
    
    # Calculate accuracy and create leaderboard
    leaderboard = []
    for user_id, correct_picks, total_picks in picks_results:
        user = User.query.get(user_id)
        accuracy = (correct_picks / total_picks * 100) if total_picks > 0 else 0
        leaderboard.append({
            'username': user.username,
            'correct_picks': correct_picks,
            'total_picks': total_picks,
            'accuracy': round(accuracy, 2)
        })
    
    # Sort by correct picks (descending) and username (ascending)
    leaderboard.sort(key=lambda x: (-x['correct_picks'], x['username']))
    
    logger.info(f'Leaderboard retrieved for user: {current_user.username}')
    return jsonify({'leaderboard': leaderboard})

@app.route('/api/stats', methods=['GET'])
@auth_required
def stats():
    user_id = request.args.get('user_id', type=int) or current_user.id
    
    # Get user's picks
    picks_query = db.session.query(
        Pick.week,
        func.count(case([(Pick.picked_team == Game.winner, 1)])).label('correct_picks'),
        func.count(Pick.id).label('total_picks')
    ).join(Game).filter(Pick.user_id == user_id).group_by(Pick.week)
    
    picks_results = picks_query.all()
    
    # Calculate weekly and overall stats
    weekly_stats = []
    total_correct = 0
    total_picks = 0
    
    for week, correct_picks, total_week_picks in picks_results:
        accuracy = (correct_picks / total_week_picks * 100) if total_week_picks > 0 else 0
        weekly_stats.append({
            'week': week,
            'correct_picks': correct_picks,
            'total_picks': total_week_picks,
            'accuracy': round(accuracy, 2)
        })
        total_correct += correct_picks
        total_picks += total_week_picks
    
    # Calculate overall accuracy
    overall_accuracy = (total_correct / total_picks * 100) if total_picks > 0 else 0
    
    logger.info(f'Stats retrieved for user: {current_user.username}')
    return jsonify({
        'weekly_stats': weekly_stats,
        'overall_stats': {
            'correct_picks': total_correct,
            'total_picks': total_picks,
            'accuracy': round(overall_accuracy, 2)
        }
    })

@app.route('/api/get_picks')
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

@app.route('/api/logout')
@auth_required
def logout():
    """Handle user logout."""
    logger.info(f'User logged out: {current_user.username}')
    logout_user()
    return jsonify({'success': True})
