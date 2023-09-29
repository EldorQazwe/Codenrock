from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User, Activity, UserActivity
from app.forms import RegistrationForm, LoginForm
from sqlalchemy.exc import OperationalError

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Укажите маршрут для входа
login_manager.login_message = 'Пожалуйста, войдите в систему, чтобы получить доступ к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
def home():
    print(url_for('static', filename='css/home.css'))
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = "Employee"
        
        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Регистрация прошла успешно! Теперь вы можете войти в систему.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    try:
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                flash("Авторизация успешна!", "success")
                login_user(user)
                session['user_id'] = user.id
                return redirect(url_for("home"))
            else:
                flash("Неверные учетные данные. Пожалуйста, проверьте свое имя пользователя и пароль.", "danger")

    except OperationalError as e:
        # Обработка ошибок базы данных
        flash("Произошла ошибка при работе с базой данных.", "danger")
        # Вывести информацию об ошибке для отладки:
        print(f"Database error: {e}")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route('/private')
@login_required
def method_name():
    return "Приватная страница"