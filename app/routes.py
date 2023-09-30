from flask import render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User
from app.forms import RegistrationForm, LoginForm


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

        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, email=email,
                        password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Регистрация прошла успешно! Теперь вы можете войти в систему.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            flash("Авторизация успешна!", "success")
            session['user_id'] = user.id
            return redirect(url_for("home"))
        else:
            flash(
                "Неверные учетные данные. Пожалуйста, проверьте свое имя пользователя и пароль.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/preline.js")
def serve_preline_js():
    return send_from_directory("../node_modules/preline/dist", "preline.js")