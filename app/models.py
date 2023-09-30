
from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # Employee [Работник] - Employer [Работодатель]
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))  # Внешний ключ к компании
    activities = db.relationship('UserActivity', back_populates='user')
    selected_goals = db.relationship('FundGoal', backref='user', lazy=True)
    
    points_balance = db.Column(db.Integer, default=0)  # Текущий баланс баллов
    
    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.role}', '{self.company_id}')"

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    employees = db.relationship('User', backref='company', lazy=True)  # Связь с работниками
    employers = db.relationship('User', backref='employer', lazy=True)  # Связь с работодателями

    def __repr__(self):
        return f"Company('{self.id}', '{self.name}')"
    
class Activity(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    users = db.relationship('UserActivity', back_populates='activity')
    
    units = db.Column(db.String(20), nullable=False)  # Единицы измерения
    active_time =  db.Column(db.Integer, nullable=False)  # Сколько кокосов за активность
    points_per_unit = db.Column(db.Integer, nullable=False)  # Сколько кокосов за активность
    active_date = db.Column(db.DateTime, default=datetime.utcnow) # Дата
    
    def __repr__(self):
        return f"Activity('{self.id}')"

class UserActivity(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), primary_key=True)
    stats = db.Column(db.String(100))
    sport_units = db.Column(db.Integer, default=0)  # Колонка для количества единиц спорта
    
    user = db.relationship('User', back_populates='activities')
    activity = db.relationship('Activity', back_populates='users')

    def __repr__(self):
        return f"User('{self.user_id}', '{self.activity_id}', '{self.stats}')"

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False) # категорию фонда (дети, животные и т.д.).
    organization_name = db.Column(db.String(100), nullable=False) #  название организации фонда.
    description = db.Column(db.Text) # описание фонда (в виде текста).
    exchanges = db.relationship('UserExchange', back_populates='fund')
    
    goals = db.relationship('FundGoal', back_populates='fund')

    def __repr__(self):
        return f"Fund('{self.id}', '{self.name}', '{self.category}', '{self.organization_name}')"
    
class FundGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount_in_rubles = db.Column(db.Float, nullable=False)
    amount_in_points = db.Column(db.Integer, nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    reached = db.Column(db.Boolean, default=False)  # Показатель достижения цели
    goal_date = db.Column(db.DateTime, nullable=False)

    fund = db.relationship('Fund', back_populates='goals')
    users = db.relationship('User', secondary='user_selected_goals', backref='selected_goals')

    def __repr__(self):
        return f"FundGoal('{self.id}', '{self.amount_in_rubles}', '{self.amount_in_points}', '{self.fund_id}', '{self.reached}', '{self.goal_date}')"

class UserExchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    
    sport_units = db.Column(db.Integer, nullable=False) # Кол-во спорт юнитов
    points_donated = db.Column(db.Integer, nullable=False) # Сумма сколько получилось при (Юниты > Баллы)
    exchange_date = db.Column(db.DateTime, default=datetime.utcnow) # Дата
    amount_in_rubles = db.Column(db.Float, nullable=False) 
    
    user = db.relationship('User', back_populates='exchanges')
    fund = db.relationship('Fund', back_populates='exchanges')

    def __repr__(self):
        return f"UserExchange('{self.id}', '{self.user_id}', '{self.fund_id}', '{self.sport_units}', '{self.points_donated}')"