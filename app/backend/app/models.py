from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=True)
    picks = db.relationship('Pick', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    espn_id = db.Column(db.String(20), unique=True, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, nullable=False)
    home_team = db.Column(db.String(3), nullable=False)
    away_team = db.Column(db.String(3), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    is_mnf = db.Column(db.Boolean, default=False)
    final_score_home = db.Column(db.Integer)
    final_score_away = db.Column(db.Integer)
    winner = db.Column(db.String(3))
    picks = db.relationship('Pick', backref='game', lazy=True)

    @property
    def is_finished(self):
        return self.winner is not None

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    picked_team = db.Column(db.String(3), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    mnf_total_points = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_correct(self):
        return self.game.winner == self.picked_team if self.game.winner else None
