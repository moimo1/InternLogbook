import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Users Table (Interns and Admins)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_text TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'intern' -- 'intern' or 'admin'
    )
''')

# Attendance Logs Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        log_type TEXT NOT NULL, -- 'IN' or 'OUT'
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
conn.commit()
conn.close()