from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import sqlite3
import datetime
import calendar

# Создание базы данных и таблиц
def create_tables():
    conn = sqlite3.connect('tutor_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            weekday INTEGER NOT NULL,
            time TEXT NOT NULL,
            subject TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    conn.commit()
    conn.close()

# Функция для старта бота
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("Добавить студента"), KeyboardButton("Показать студентов")],
        [KeyboardButton("Добавить расписание"), KeyboardButton("Показать расписание")],
        [KeyboardButton("Дополнительные материалы")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Привет! Я бот-репетитор. Выберите действие:', reply_markup=reply_markup)

# Функция для добавления студента
async def add_student(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите данные студента в формате: Имя Класс")
    context.user_data['action'] = 'add_student'

# Функция для отображения студентов
async def show_students(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect('tutor_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, grade FROM students')
    rows = cursor.fetchall()
    students_text = '\n'.join([f"{row[0]} - {row[1]}" for row in rows])
    conn.close()
    await update.message.reply_text(students_text or 'Список студентов пуст.')

# Функция для добавления расписания
async def add_schedule(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Выберите день недели", reply_markup=create_weekday_keyboard())
    context.user_data['action'] = 'add_schedule'

# Функция для отображения расписания
async def show_schedule(update: Update, context: CallbackContext) -> None:
    today = datetime.date.today()
    weekday = today.weekday()  # 0 - Monday, 6 - Sunday
    start_of_week = today - datetime.timedelta(days=weekday)

    conn = sqlite3.connect('tutor_bot.db')
    cursor = conn.cursor()
    schedule_text = ''

    for i in range(7):
        current_day = start_of_week + datetime.timedelta(days=i)
        cursor.execute('SELECT students.name, schedule.subject, schedule.time FROM schedule JOIN students ON schedule.student_id = students.id WHERE schedule.weekday=?', (i,))
        rows = cursor.fetchall()
        day_schedule = '\n'.join([f"{row[0]} - {row[1]} в {row[2]}" for row in rows])
        schedule_text += f"{current_day.strftime('%A, %d %B %Y')}\n{day_schedule or 'Нет занятий'}\n\n"

    conn.close()
    await update.message.reply_text(schedule_text)

# Создание клавиатуры для выбора дня недели
def create_weekday_keyboard():
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    keyboard = [[InlineKeyboardButton(day, callback_data=f'select_weekday_{i}') for i, day in enumerate(weekdays)]]
    return InlineKeyboardMarkup(keyboard)

# Создание клавиатуры для выбора времени
def create_time_keyboard():
    times = [f"{hour:02d}:{minute:02d}" for hour in range(8, 21) for minute in (0, 30)]
    keyboard = [[InlineKeyboardButton(time, callback_data=f'select_time_{time}')] for time in times]
    return InlineKeyboardMarkup(keyboard)

# Создание клавиатуры для выбора предмета
def create_subject_keyboard():
    subjects = ['Информатика', 'Математика', 'Физика']
    keyboard = [[InlineKeyboardButton(subject, callback_data=f'select_subject_{subject}')] for subject in subjects]
    return InlineKeyboardMarkup(keyboard)

# Обработка выбора дня недели
async def select_weekday(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    weekday = int(query.data.split('_')[-1])
    context.user_data['weekday'] = weekday
    await query.edit_message_text(text=f"Выбранный день: {calendar.day_name[weekday]}. Выберите время занятия:", reply_markup=create_time_keyboard())

# Обработка выбора времени
async def select_time(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    time = query.data.split('_')[-1]
    context.user_data['time'] = time
    await query.edit_message_text(text=f"Выбранное время: {time}. Выберите предмет:", reply_markup=create_subject_keyboard())

# Обработка выбора предмета
async def select_subject(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split('_')[-1]
    context.user_data['subject'] = subject
    await query.edit_message_text(text=f"Выбранный предмет: {subject}. Введите имя студента:")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    action = context.user_data.get('action')

    if action == 'add_student':
        try:
            name, grade = update.message.text.split()
            conn = sqlite3.connect('tutor_bot.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO students (name, grade) VALUES (?, ?)', (name, grade))
            conn.commit()
            conn.close()
            await update.message.reply_text(f'Студент {name} добавлен.')
        except ValueError:
            await update.message.reply_text('Пожалуйста, используйте формат: Имя Класс')

    elif action == 'add_schedule':
        try:
            name = update.message.text
            weekday = context.user_data.get('weekday')
            time = context.user_data.get('time')
            subject = context.user_data.get('subject')
            if weekday is None:
                await update.message.reply_text('Сначала выберите день недели.')
                return
            if time is None:
                await update.message.reply_text('Сначала выберите время.')
                return
            if subject is None:
                await update.message.reply_text('Сначала выберите предмет.')
                return

            conn = sqlite3.connect('tutor_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM students WHERE name=?', (name,))
            student_id = cursor.fetchone()
            if student_id:
                cursor.execute('INSERT INTO schedule (student_id, weekday, time, subject) VALUES (?, ?, ?, ?)', (student_id[0], weekday, time, subject))
                conn.commit()
                await update.message.reply_text(f'Расписание для {name} на {calendar.day_name[weekday]} в {time} по предмету {subject} добавлено.')
            else:
                await update.message.reply_text('Студент не найден.')
            conn.close()
        except ValueError:
            await update.message.reply_text('Пожалуйста, используйте формат: Имя')

    context.user_data['action'] = None

# Функция для отображения дополнительных материалов
async def show_materials(update: Update, context: CallbackContext) -> None:
    materials_text = "Дополнительные материалы:\n\n" \
                     "1. [Сайт с учебными материалами](https://example.com)\n" \
                     "2. [Видеоуроки на YouTube](https://youtube.com)\n" \
                     "3. [Документы и файлы](https://drive.google.com)\n\n" \
                     "По всем вопросам обращайтесь к преподавателю @Lock1ng1"
    await update.message.reply_text(materials_text, disable_web_page_preview=True)

# Основная функция
def main():
    # Создайте базы данных и таблицы, если их нет
    create_tables()

    # Создайте экземпляр Application и передайте ему токен вашего бота.
    application = Application.builder().token("7106663211:AAF60a49kmz1ccKFaf23M0QYD8zK0ecquH8").build()

    # Зарегистрируйте обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Добавить студента$'), add_student))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Показать студентов$'), show_students))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Добавить расписание$'), add_schedule))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Показать расписание$'), show_schedule))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Дополнительные материалы$'), show_materials))
    application.add_handler(CallbackQueryHandler(select_weekday, pattern='^select_weekday_'))
    application.add_handler(CallbackQueryHandler(select_time, pattern='^select_time_'))
    application.add_handler(CallbackQueryHandler(select_subject, pattern='^select_subject_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запустите бота
    application.run_polling()

if __name__ == '__main__':
    main()
