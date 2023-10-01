from datetime import timedelta
from flask import render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import *
from app.forms import RegistrationForm, LoginForm
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc, or_


from flask_login import LoginManager, login_user, login_required, logout_user, current_user
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Укажите маршрут для входа
login_manager.login_message = 'Пожалуйста, войдите в систему, чтобы получить доступ к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Путь для авторизации
@app.route('/auth', methods=['GET'])
def authorize():
    user_id = request.args.get('user_id')

    # Проверяем существование пользователя в вашей базе данных
    # и проводим процесс авторизации
    # ...

    return "Авторизация успешна"


@app.route("/")
@app.route("/home")
@login_required
def home():

    user = User.query.get(current_user.id)
    company = Company.query.get(user.company_id)
    department = Department.query.get(user.department_id)

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

    total_points = int(user.points_balance +
                       sum(donation.amount_points for donation in user.donations))

    data = {
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "balance": user.points_balance,
            "total_donations": int(sum(donation.amount_points for donation in user.donations)),
            "personal_rating": user_position,
            "total_points": total_points
        },
        "company": {
            "id": company.id,
            "company": company.name
        },
        "department": {
            "id": department.id,
            "name": department.name,
        },
        "activity_types": ActivityType.query.all()
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

    department_ratings = db.session.query(
        Department.name,
        func.sum(Donation.amount_points).label('total_donations')
    ).join(User, Department.id == User.department_id).join(Donation, User.id == Donation.user_id).filter(Department.company_id == current_user.company_id).group_by(Department.id).order_by(func.sum(Donation.amount_points).desc()).all()

    print(current_user.id, company.departments, department_ratings)

    return "top_donors"


@app.route('/rating/filter',  methods=["GET"])
def filter_points_added():
    try:
        # Получаем параметры из запроса
        activity_id = request.args.get('activity', type=int)
        date_start_unix = request.args.get('date_start', type=int)
        date_end_unix = request.args.get('date_end', type=int)

        # Преобразуем метки времени в объекты datetime
        date_start = datetime.utcfromtimestamp(date_start_unix)
        date_end = datetime.utcfromtimestamp(date_end_unix)

        # Фильтруем записи в базе данных для текущего пользователя
        if activity_id == 0:
            # Если activity_id = 0, фильтруем по всем activity
            aggregated_points = db.session.query(PointsAdded.user_id,
                                                 User.first_name,
                                                 User.last_name,
                                                 func.sum(PointsAdded.points_amount).label('total_points')) \
                .join(User, PointsAdded.user_id == User.id) \
                .filter(PointsAdded.log_date.between(date_start, date_end)) \
                .group_by(PointsAdded.user_id, User.first_name, User.last_name) \
                .all()
        else:
            # Иначе фильтруем только по указанному activity_id
            aggregated_points = db.session.query(PointsAdded.user_id,
                                                 User.first_name,
                                                 User.last_name,
                                                 func.sum(PointsAdded.points_amount).label('total_points')) \
                .join(User, PointsAdded.user_id == User.id) \
                .filter(or_(PointsAdded.activity_type_id == activity_id, activity_id == 0),
                        PointsAdded.log_date.between(date_start, date_end)) \
                .group_by(PointsAdded.user_id, User.first_name, User.last_name) \
                .all()

        # Преобразуем результат в формат JSON
        result = [{"user": {
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
        }, "total_points": total_points} for user_id, first_name, last_name, total_points in aggregated_points]

        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})


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


@app.route('/balance')
def add_balance():

    # Идентификаторы пользователей, для которых создаются данные
    user_ids = [1, 2]

    points_added_data = []
    from random import randint

    for user_id in user_ids:
        for days_interval in [1, 7, 30, 60]:
            # Создаем точку данных для каждого интервала
            points_added_data.append({
                "user_id": user_id,
                "activity_type_id": randint(1, 6),
                # Здесь укажи количество добавленных баллов
                "points_amount": randint(10, 1000),
                "log_date": datetime.utcnow() - timedelta(days=days_interval)
            })

    # Добавляем данные в базу данных
    for points_data in points_added_data:
        points_added = PointsAdded(**points_data)
        db.session.add(points_added)

    # Сохраняем изменения в базе данных
    db.session.commit()

    return "Приватная страница"


@app.route('/execute')
def execute():

    # Создаем 10 пользователей
    users_data = [
        {"first_name": "John", "last_name": "Doe", "username": "john_doe",
            "email": "john@example.com", "password": "password1", "role": "user", "points_balance": 100},
        {"first_name": "Jane", "last_name": "Doe", "username": "jane_doe", "email": "jane@example.com",
            "password": "password2", "role": "admin", "points_balance": 150},
        # Добавь еще 8 пользователей с аналогичной структурой данных
    ]

    for user_data in users_data:
        user = User(**user_data)
        db.session.add(user)

    # Создаем 10 компаний
    companies_data = [
        {"name": "Company1", "total_balance": 100000, "conversion_factor": 2},
        {"name": "Company2", "total_balance": 150000, "conversion_factor": 3},
        # Добавь еще 8 компаний с аналогичной структурой данных
    ]

    for company_data in companies_data:
        company = Company(**company_data)
        db.session.add(company)

    # Создаем 10 отделов
    departments_data = [
        {"name": "Department1", "company_id": 1},
        {"name": "Department2", "company_id": 2},
        # Добавь еще 8 отделов с аналогичной структурой данных
    ]

    for department_data in departments_data:
        department = Department(**department_data)
        db.session.add(department)

    # Создаем 10 типов активностей
    activity_types_data = [
        {"name": "Running", "units": "Minutes", "points_per_unit": 5},
        {"name": "Swimming", "units": "Minutes", "points_per_unit": 7},
        # Добавь еще 8 типов активностей с аналогичной структурой данных
    ]

    for activity_type_data in activity_types_data:
        activity_type = ActivityType(**activity_type_data)
        db.session.add(activity_type)

    # Создаем 10 активностей
    activities_data = [
        {"user_id": 1, "amount_points": 50, "reached": False, "activity_type_id": 1},
        {"user_id": 2, "amount_points": 30, "reached": True, "activity_type_id": 2},
        # Добавь еще 8 активностей с аналогичной структурой данных
    ]

    for activity_data in activities_data:
        activity = Activity(**activity_data)
        db.session.add(activity)

    # Создаем 10 фондов
    funds_data = [
        {"organization_name": "Fund1", "category": "Animals", "location": "City1",
            "description": "Description1", "phone_number": "1234567890"},
        {"organization_name": "Fund2", "category": "Children", "location": "City2",
            "description": "Description2", "phone_number": "0987654321"},
        # Добавь еще 8 фондов с аналогичной структурой данных
    ]

    for fund_data in funds_data:
        fund = Fund(**fund_data)
        db.session.add(fund)

    # Создаем 10 целей фонда
    fund_goals_data = [
        {"fund_id": 1, "user_id": 1, "name": "Goal1", "collected_amount": 500,
            "target_amount": 1000, "reached": False, "goal_date": datetime.utcnow()},
        {"fund_id": 2, "user_id": 2, "name": "Goal2", "collected_amount": 300,
            "target_amount": 500, "reached": True, "goal_date": datetime.utcnow()},
        # Добавь еще 8 целей фонда с аналогичной структурой данных
    ]

    for fund_goal_data in fund_goals_data:
        fund_goal = FundGoal(**fund_goal_data)
        db.session.add(fund_goal)

    # Создаем 10 пожертвований
    donations_data = [
        {"amount_points": 50, "user_id": 1, "fund_goal_id": 1,
            "donation_date": datetime.utcnow()},
        {"amount_points": 30, "user_id": 2, "fund_goal_id": 2,
            "donation_date": datetime.utcnow()},
        # Добавь еще 8 пожертвований с аналогичной структурой данных
    ]

    for donation_data in donations_data:
        donation = Donation(**donation_data)
        db.session.add(donation)

    # Сохраняем изменения в базе данных
    db.session.commit()

    return "Приватная страница"


@app.route('/activity_types_data')
def activity_types_data():

    # Создание объектов ActivityType
    activity_types_data = [
        {"name": "Бег", "units": "Километры", "points_per_unit": 5},
        {"name": "Ходьба", "units": "Шаги", "points_per_unit": 3},
        {"name": "Плавание", "units": "Бассейн-длина", "points_per_unit": 7},
        {"name": "Силовые упражнения", "units": "Подходы", "points_per_unit": 6},
        {"name": "Катание на роликах", "units": "Километры", "points_per_unit": 4},
        {"name": "Езда на велосипеде", "units": "Километры", "points_per_unit": 5},
        {"name": "Футбол", "units": "Матчи", "points_per_unit": 8},
        {"name": "Танцы", "units": "Минуты", "points_per_unit": 6},
        {"name": "Фитнес", "units": "Сеансы", "points_per_unit": 5},
        {"name": "Лыжный спорт", "units": "Километры", "points_per_unit": 7},
        {"name": "Хоккей", "units": "Матчи", "points_per_unit": 8},
        {"name": "Волейбол", "units": "Матчи", "points_per_unit": 6},
        {"name": "Баскетбол", "units": "Матчи", "points_per_unit": 7},
        {"name": "Легкая атлетика", "units": "Дисциплины", "points_per_unit": 6},
        {"name": "Настольный теннис", "units": "Сеты", "points_per_unit": 4},
        {"name": "Йога", "units": "Сеансы", "points_per_unit": 4},
        {"name": "Бокс", "units": "Раунды", "points_per_unit": 5},
    ]

    # Вставка данных в базу данных
    for activity_data in activity_types_data:
        new_activity_type = ActivityType(**activity_data)
        db.session.add(new_activity_type)

    # Фиксация изменений в базе данных
    db.session.commit()

    return "Приватная страница"
