import sqlite3

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

create_tables()

