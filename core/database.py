import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL instance
    using the environment configuration details.
    """
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def init_db():
    """
    Initializes the system schema definitions. Sets up standard
    rosters, logs, configurations, the excused absence tracker,
    and approved overtime allowances.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # 1. System Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    roles VARCHAR(20) DEFAULT 'intern',
                    is_active INT DEFAULT 1
                );
            ''')

            # 2. Daily Attendance Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    log_type VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                );
            ''')

            # 3. System Global Settings Configurations Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL
                );
            ''')

            # 4. Excused Absences Resolution Schema Matrix
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS excused_absences (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    absence_date DATE NOT NULL,
                    reason TEXT DEFAULT 'Excused Absence',
                    UNIQUE(user_id, absence_date)
                );
            ''')

            # 5. Approved Overtime Tracking Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS approved_overtime (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    overtime_date DATE NOT NULL,
                    hours_approved NUMERIC(4,2) NOT NULL,
                    UNIQUE(user_id, overtime_date)
                );
            ''')

            # Seed default emergency global supervisor dashboard credentials if missing
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (username, password, roles, is_active) VALUES (%s, %s, %s, %s)",
                    ('admin', 'admin123', 'admin', 1)
                )

            # Seed default schedule rules if the settings table is fresh/empty
            cursor.execute("SELECT value FROM system_settings WHERE key = 'schedule_rules'")
            if not cursor.fetchone():
                default_sched = {
                    "MWF": {"start": "08:00", "end": "17:00"},
                    "TF":  {"start": "08:00", "end": "17:00"}
                }
                cursor.execute(
                    "INSERT INTO system_settings (key, value) VALUES ('schedule_rules', %s)",
                    (json.dumps(default_sched),)
                )

        conn.commit()