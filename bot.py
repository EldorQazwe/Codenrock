from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiogram.types import PhotoSize

storage = MemoryStorage()

from app import app 
from app import db  

# Импортируйте вашу модель User
from app.models import User, Activity, ActivityType

# Создайте экземпляр бота и диспетчера
bot = Bot(token='6444758530:AAFbJ1ocpRq-NJmPgGUX1AyUyghRUMdNESc')
dp = Dispatcher(bot, storage=storage)

from aiogram.dispatcher.middlewares import BaseMiddleware

activity_types_data = [
    {"name": "Бег", "units": "Минут", "points_per_unit": 5},
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

class AuthMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        telegram_id = message.from_user.id
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=int(telegram_id)).first()

        data['user'] = user  # передаем пользователя в данные для последующих обработчиков

        if user:
            # Если пользователь авторизован, добавьте что-то в данные (если нужно)
            data['is_authorized'] = True
        else:
            # Если пользователь не найден, добавьте что-то в данные (если нужно)
            data['is_authorized'] = False

# Добавьте middleware к диспетчеру
dp.middleware.setup(AuthMiddleware())

class ActivityForm(StatesGroup):
    ChooseActivity = State()
    EnterAmount = State()
    UploadPhoto = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, user, is_authorized):
    
    if not is_authorized: 
        return await message.answer("Вы не авторизованы")
    
    await message.answer(f"Привет, {user.first_name}!\nДавайте начнем создание активности.")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for activity_data in activity_types_data:
        keyboard.add(types.KeyboardButton(activity_data["name"]))

    await ActivityForm.ChooseActivity.set()
    await message.answer("Выберите тип активности:", reply_markup=keyboard)

# Обработчик выбора типа активности
@dp.message_handler(state=ActivityForm.ChooseActivity)
async def choose_activity(message: types.Message, state: FSMContext):
    activity_name = message.text
    activity_data = next((item for item in activity_types_data if item["name"] == activity_name), None)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Назад к категориям"))

    if activity_data:
        await state.update_data(activity_type=activity_data)
        await ActivityForm.next()
        await message.answer(f"Отлично! Теперь укажите, сколько времени вы занимались {activity_name} ({activity_data['units']}):", reply_markup=keyboard)

# Обработчик кнопки "Назад к категориям"
@dp.message_handler(lambda message: message.text == "Назад к категориям", state=ActivityForm.EnterAmount)
async def back_to_categories(message: types.Message, state: FSMContext):
    await ActivityForm.ChooseActivity.set()
    
    # Добавляем клавиатуру с категориями активности
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for activity_data in activity_types_data:
        keyboard.add(types.KeyboardButton(activity_data["name"]))
    

    await message.answer("Выберите тип активности:", reply_markup=keyboard)
    
    await ActivityForm.ChooseActivity.set()
    
    
# Обработчик ввода времени
@dp.message_handler(state=ActivityForm.EnterAmount)
async def enter_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        await state.update_data(amount=amount)
        await ActivityForm.next()
        
        # Добавляем кнопку "Назад" для возврата к выбору категории активности
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Назад к категориям"))
        
        await message.answer("Отправьте фото подтверждения активности:", reply_markup=keyboard)
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

# Обработчик кнопки "Назад к категориям" при вводе времени
@dp.message_handler(lambda message: message.text == "Назад к категориям", state=ActivityForm.UploadPhoto)
async def back_to_categories_from_enter_amount(message: types.Message, state: FSMContext):
    await ActivityForm.ChooseActivity.set()
    
    # Добавляем клавиатуру с категориями активности
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for activity_data in activity_types_data:
        keyboard.add(types.KeyboardButton(activity_data["name"]))
    
    await message.answer("Выберите тип активности:", reply_markup=keyboard)

    await ActivityForm.ChooseActivity.set()
    
# Обработчик загрузки фото
@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=ActivityForm.UploadPhoto)
async def upload_photo(message: types.Message, state: FSMContext, user, is_authorized):
    # В этом месте вы можете сохранить фото и другие данные в базу данных
    user_id = message.from_user.id
    data = await state.get_data()
    
    activity_type_data = data.get('activity_type')
    amount = data.get('amount')

    with app.app_context():
        activity_type = ActivityType.query.filter_by(name=activity_type_data['name']).first()

        new_activity = Activity(user_id=user_id, amount_points=amount, activity_type_id=activity_type.id)
        db.session.add(new_activity)
        db.session.commit()

    await state.finish()
    await message.answer("Активность успешно добавлена!")
    
# Запустите бот
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
