from flask import render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import *
from app.forms import RegistrationForm, LoginForm
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc


from flask_login import LoginManager, login_user, login_required, logout_user, current_user
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Укажите маршрут для входа
login_manager.login_message = 'Пожалуйста, войдите в систему, чтобы получить доступ к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@app.route("/home")
@login_required
def home():

    user = User.query.get(current_user.id)
    company = Company.query.get(user.company_id)

    all_donors_query = (
        User.query
        .join(Donation)
        .group_by(User.id)
        .order_by(desc(func.sum(Donation.amount_points)))
        .add_columns(User.id, User.first_name, User.last_name, func.sum(Donation.amount_points).label('total_donations'))
        .all()
    )

    user_position = None
    for index, donor in enumerate(all_donors_query):
        if donor.id == current_user.id:
            user_position = index + 1

    data = {
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "balance": user.points_balance,
            "total_donations": sum(donation.amount_points for donation in user.donations),
            "personal_rating": user_position
        },
        "company": {
            "id": company.id,
            "company": company.name
        }
    }
    return render_template("home.html", **data)


@app.route("/get_top_donors")
def get_top_donors():

    top_donors_query = (
        User.query
        .join(Donation)
        .group_by(User.id)
        .order_by(desc(func.sum(Donation.amount_points)))
        .limit(10)
        .add_columns(User.id, User.first_name, User.last_name, func.sum(Donation.amount_points).label('total_donations'))
        .all()
    )

    top_donors = [
        {"id": donor.id, "first_name": donor.first_name,
            "last_name": donor.last_name, "total_donations": donor.total_donations}
        for donor in top_donors_query
    ]
    return top_donors


@login_required
@app.route("/get_top_department")
def get_top_department():

    user = User.query.get(current_user.id)
    company = Company.query.get(user.company_id)

    print(company)

    return "top_donors"

# @login_required
# @app.route('/mrating')
# def mrating():
#     user_id = current_user.id


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = "Employee"

        # Check if the username or email is already registered
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "Пользователь с таким именем уже существует. Выберите другое имя.", "danger")
        elif existing_email:
            flash(
                "Пользователь с таким email уже зарегистрирован. Используйте другой email.", "danger")
        else:
            # Hash the password and add the new user to the database
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(username=username, email=email,
                            password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()

            flash(
                "Регистрация прошла успешно! Теперь вы можете войти в систему.", "success")
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

            # if user and check_password_hash(user.password, password):
            if user and True:
                flash("Авторизация успешна!", "success")
                login_user(user)
                session['user_id'] = user.id
                return redirect(url_for("home"))
            else:
                flash(
                    "Неверные учетные данные. Пожалуйста, проверьте свое имя пользователя и пароль.", "danger")

    except OperationalError as e:
        # Обработка ошибок базы данных
        flash("Произошла ошибка при работе с базой данных.", "danger")
        # Вывести информацию об ошибке для отладки:
        print(f"Database error: {e}")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/preline.js")
def serve_preline_js():
    return send_from_directory("../node_modules/preline/dist", "preline.js")


@app.route("/tw-elements.js")
def serve_twelements_js():
    return send_from_directory("../node_modules/tw-elements/dist/js", "tw-elements.umd.min.js")


@app.route('/private')
@login_required
def method_name():

    return "Приватная страница"


@app.route('/execute')
def execute():

    # Создание тестовых данных для модели User
    user1 = User(first_name='John', last_name='Doe', username='johndoe', email='john.doe@example.com',
                 password='password123', role='user', company_id=1, department_id=1, points_balance=100)
    user2 = User(first_name='Jane', last_name='Smith', username='janesmith', email='jane.smith@example.com',
                 password='password456', role='admin', company_id=2, department_id=2, points_balance=150)

    # Создание тестовых данных для модели Company
    company1 = Company(name='Company A', total_balance=1000,
                       conversion_factor=2)
    company2 = Company(name='Company B', total_balance=1500,
                       conversion_factor=1)

    # Создание тестовых данных для модели Department
    department1 = Department(name='HR', company_id=1)
    department2 = Department(name='IT', company_id=2)

    # Создание тестовых данных для модели Activity
    activity1 = Activity(name='Meeting', user_id=1, units='Minutes',
                         amount_points=50, reached=False, active_date=datetime.utcnow())
    activity2 = Activity(name='Coding', user_id=2, units='Minutes',
                         amount_points=75, reached=True, active_date=datetime.utcnow())

    # Создание тестовых данных для модели Fund
    fund1 = Fund(organization_name='Animal Shelter', category='Animals', location='City A',
                 description='A shelter for stray animals', phone_number='123-456-7890')
    fund2 = Fund(organization_name='Children Foundation', category='Children', location='City B',
                 description='Supporting children in need', phone_number='987-654-3210')

    # Создание тестовых данных для модели FundGoal
    fund_goal1 = FundGoal(fund_id=1, user_id=1, name='Animal Shelter Goal',
                          collected_amount=500, target_amount=1000, reached=False, goal_date=datetime.utcnow())
    fund_goal2 = FundGoal(fund_id=2, user_id=2, name='Children Foundation Goal',
                          collected_amount=1500, target_amount=2000, reached=True, goal_date=datetime.utcnow())

    # Создание тестовых данных для модели Donation
    donation1 = Donation(amount_points=50, user_id=1,
                         fund_goal_id=1, donation_date=datetime.utcnow())
    donation2 = Donation(amount_points=100, user_id=2,
                         fund_goal_id=2, donation_date=datetime.utcnow())

    # Добавление данных в базу данных
    db.session.add_all([user1, user2, company1, company2, department1, department2,
                       activity1, activity2, fund1, fund2, fund_goal1, fund_goal2, donation1, donation2])
    db.session.commit()

    return "Приватная страница"
