
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # Employee [Работник] - Employer [Работодатель]
    activities = db.relationship('UserActivity', back_populates='user')
    sport_units = db.Column(db.Integer, default=0)  # Колонка для количества единиц спорта
    
    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.role}')"
 
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('UserActivity', back_populates='activity')

    def __repr__(self):
        return f"Activity('{self.id}')"

class UserActivity(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    stats = db.Column(db.String(100))
    user = db.relationship('User', back_populates='activities')
    activity = db.relationship('Activity', back_populates='users')
    
    def __repr__(self):
        return f"User('{self.user_id}')"