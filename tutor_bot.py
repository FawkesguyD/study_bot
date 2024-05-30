from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import sqlite3
import datetime
import calendar

def create_tables():
    """
    Creates the tables 'students' and 'schedule' in the 'tutor_bot.db' database.
    If the tables already exist, they will not be created again.

    The 'students' table has the following columns:
        - id: INTEGER, Primary Key, Auto Increment
        - name: TEXT, Not Null
        - grade: TEXT, Not Null

    The 'schedule' table has the following columns:
        - id: INTEGER, Primary Key, Auto Increment
        - student_id: INTEGER, Not Null, Foreign Key referencing 'students.id'
        - weekday: INTEGER, Not Null
        - time: TEXT, Not Null
        - subject: TEXT, Not Null

    This function commits the changes to the database and then closes the connection.
    """
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

async def start(update: Update, context: CallbackContext) -> None:
    """
    Handles the /start command. Sends a welcome message with options for the user to choose from.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    keyboard = [
        [KeyboardButton("Добавить студента"), KeyboardButton("Показать студентов")],
        [KeyboardButton("Добавить расписание"), KeyboardButton("Показать расписание")],
        [KeyboardButton("Дополнительные материалы")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Привет! Я бот-репетитор. Выберите действие:', reply_markup=reply_markup)

async def add_student(update: Update, context: CallbackContext) -> None:
    """
    Handles the action to add a student. Prompts the user to enter the student's data in a specific format.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    await update.message.reply_text("Введите данные студента в формате: Имя Класс")
    context.user_data['action'] = 'add_student'

async def show_students(update: Update, context: CallbackContext) -> None:
    """
    Retrieves and displays a list of students from the 'students' table in the database.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    conn = sqlite3.connect('tutor_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, grade FROM students')
    rows = cursor.fetchall()
    students_text = '\n'.join([f"{row[0]} - {row[1]}" for row in rows])
    conn.close()
    await update.message.reply_text(students_text or 'Список студентов пуст.')

async def add_schedule(update: Update, context: CallbackContext) -> None:
    """
    Initiates the process of adding a schedule. Prompts the user to select a day of the week.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    await update.message.reply_text("Выберите день недели", reply_markup=create_weekday_keyboard())
    context.user_data['action'] = 'add_schedule'

async def show_schedule(update: Update, context: CallbackContext) -> None:
    """
    Retrieves and displays the schedule for the current week from the 'schedule' table in the database.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
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

def create_weekday_keyboard():
    """
    Creates an inline keyboard with buttons for each day of the week.

    Returns:
        InlineKeyboardMarkup: The inline keyboard markup with weekday buttons.
    """
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    keyboard = [[InlineKeyboardButton(day, callback_data=f'select_weekday_{i}') for i, day in enumerate(weekdays)]]
    return InlineKeyboardMarkup(keyboard)

def create_time_keyboard():
    """
    Creates an inline keyboard with buttons for selecting time slots from 08:00 to 20:30.

    Returns:
        InlineKeyboardMarkup: The inline keyboard markup with time slot buttons.
    """
    times = [f"{hour:02d}:{minute:02d}" for hour in range(8, 21) for minute in (0, 30)]
    keyboard = [[InlineKeyboardButton(time, callback_data=f'select_time_{time}')] for time in times]
    return InlineKeyboardMarkup(keyboard)

def create_subject_keyboard():
    """
    Creates an inline keyboard with buttons for selecting subjects.

    Returns:
        InlineKeyboardMarkup: The inline keyboard markup with subject buttons.
    """
    subjects = ['Информатика', 'Математика', 'Физика']
    keyboard = [[InlineKeyboardButton(subject, callback_data=f'select_subject_{subject}')] for subject in subjects]
    return InlineKeyboardMarkup(keyboard)

async def select_weekday(update: Update, context: CallbackContext) -> None:
    """
    Handles the selection of a weekday. Prompts the user to select a time slot.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    query = update.callback_query
    await query.answer()
    weekday = int(query.data.split('_')[-1])
    context.user_data['weekday'] = weekday
    await query.edit_message_text(text=f"Выбранный день: {calendar.day_name[weekday]}. Выберите время занятия:", reply_markup=create_time_keyboard())

async def select_time(update: Update, context: CallbackContext) -> None:
    """
    Handles the selection of a time slot. Prompts the user to select a subject.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    query = update.callback_query
    await query.answer()
    time = query.data.split('_')[-1]
    context.user_data['time'] = time
    await query.edit_message_text(text=f"Выбранное время: {time}. Выберите предмет:", reply_markup=create_subject_keyboard())

async def select_subject(update: Update, context: CallbackContext) -> None:
    """
    Handles the selection of a subject. Prompts the user to enter the student's name.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    query = update.callback_query
    await query.answer()
    subject = query.data.split('_')[-1]
    context.user_data['subject'] = subject
    await query.edit_message_text(text=f"Выбранный предмет: {subject}. Введите имя студента:")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Handles text messages for adding students and schedules based on the current action stored in user_data.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
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

async def show_materials(update: Update, context: CallbackContext) -> None:
    """
    Displays additional materials for the students, including links to educational websites and resources.

    Args:
        update (Update): The update object that contains information about the incoming update.
        context (CallbackContext): The context object that contains information about the current context of the update.
    """
    materials_text = "Дополнительные материалы:\n\n" \
                     "1. [Сайт с учебными материалами](https://example.com)\n" \
                     "2. [Видеоуроки на YouTube](https://youtube.com)\n" \
                     "3. [Документы и файлы](https://drive.google.com)\n\n" \
                     "По всем вопросам обращайтесь к преподавателю @Lock1ng1"
    await update.message.reply_text(materials_text, disable_web_page_preview=True)

def main():
    """
    Main function to set up the bot, including creating the database tables and registering command handlers.
    Runs the bot's polling loop to continuously check for new updates.
    """
    # Create database tables if they don't exist
    create_tables()

    # Create an Application instance and pass the bot token
    application = Application.builder().token("7106663211:AAF60a49kmz1ccKFaf23M0QYD8zK0ecquH8").build()

    # Register command handlers
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

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()

