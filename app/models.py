
from flask_login import UserMixin
from datetime import datetime
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    points_balance = db.Column(db.Integer, default=0)
    
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    donations = db.relationship('Donation', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.role}', '{self.company_id}')"

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    total_balance = db.Column(db.Integer, nullable=False)
    conversion_factor = db.Column(db.Integer, nullable=False, default=1)
    
    departments = db.relationship('Department', backref='company', lazy=True)

    def __repr__(self):
        return f"Company('{self.id}', '{self.name}')"

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employees = db.relationship('User', backref='department', lazy=True)

    def __repr__(self):
        return f"Department('{self.id}', '{self.name}', '{self.company_id}')"


class ActivityType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    units = db.Column(db.String(20), nullable=False, default="Минут")
    points_per_unit = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f"ActivityType('{self.name}')"


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # active_time = db.Column(db.Integer, nullable=False)
    amount_points = db.Column(db.Integer, nullable=False)
    
    # points_per_unit = db.Column(db.Integer, nullable=False)
    reached = db.Column(db.Boolean, default=False) # Выполнено ли
    active_date = db.Column(db.DateTime, default=datetime.utcnow)

    activity_type = db.relationship('ActivityType', backref='activities')

    def __repr__(self):
        return f"Activity('{self.id}')"

# Тут будут все фонды 
class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(50), unique=True, nullable=False) # Название огранизации
    category = db.Column(db.String(50), nullable=False) # (животные, дети, пожилые и т.д.)
    location = db.Column(db.String(100), nullable=False) # Местоположения 
    description = db.Column(db.String(300))  # Описание фонда
    phone_number = db.Column(db.String(12)) # Телефон фонда
    
    def __repr__(self):
        return f"Fund('{self.id}', '{self.name}', '{self.category}', '{self.organization_name}')"

# Здесь цели фонда, то сколько надо будет собрать на ту или инную цель 
class FundGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False) # Ссылки 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Ссылки

    name = db.Column(db.String(50), unique=True, nullable=False)

    collected_amount =  db.Column(db.Float, default=0.0)  # Сумма, которую уже удалось собрать
    target_amount = db.Column(db.Float, nullable=False)  # Общая целевая сумма для достижения
    
    reached = db.Column(db.Boolean, default=False) # Выполнено ли
    goal_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Дата создания цели
    
    def __repr__(self):
        return f"FundGoal('{self.id}', '{self.fund_id}', '{self.reached}', '{self.goal_date}')"

# История пожертовавания в ту или инную компанию, какого-то человека
class Donation(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    amount_points = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_goal_id = db.Column(db.Integer, db.ForeignKey('fund_goal.id'), nullable=False)
    donation_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"Donation('{self.id}', '{self.amount_points}', '{self.user_id}', '{self.fund_goal_id}', '{self.donation_date}')"

# class UserExchange(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     fund_id = db.Column(db.Integer, db.ForeignKey('fund_goal.id'), nullable=False)
#     activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
#     sport_units = db.Column(db.Integer, nullable=False)
#     points_donated = db.Column(db.Integer, nullable=False)
#     exchange_date = db.Column(db.DateTime, default=datetime.utcnow)
#     amount_in_rubles = db.Column(db.Float, nullable=False)
    
#     def __repr__(self):
#         return f"UserExchange('{self.id}', '{self.user_id}', '{self.fund_id}', '{self.sport_units}', '{self.points_donated}')"
