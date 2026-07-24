import os
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import has_app_context, g

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL instance
    using the environment configuration details. Uses Flask's request context
    'g' if available to avoid connection leaks during requests.
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set. Please set it in your environment or docker-compose.yaml.")

    if has_app_context():
        if 'db_conn' not in g:
            g.db_conn = psycopg2.connect(db_url)
        return g.db_conn
    else:
        return psycopg2.connect(db_url)

def init_db():
    """
    Initializes the system schema definitions. Sets up standard
    rosters, logs, configurations, the excused absence tracker,
    and approved overtime allowances.
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL environment variable is not set. Skipping DB initialization.")
        return

    # Wait for database to be ready (up to 15 seconds) - standard local/Docker-compose practice
    conn = None
    retries = 5
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(db_url)
            break
        except psycopg2.OperationalError as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to connect to the database after {retries} retries: {e}")
            print(f"Database not ready yet. Retrying in 3 seconds... ({retries - attempt - 1} retries left)")
            time.sleep(3)

    try:
        with conn:
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
                        "MTW": {"start": "08:00", "end": "17:00", "break_start": "12:00", "break_end": "13:00"},
                        "ThF":  {"start": "08:00", "end": "17:00", "break_start": "12:00", "break_end": "13:00"}
                    }
                    cursor.execute(
                        "INSERT INTO system_settings (key, value) VALUES ('schedule_rules', %s)",
                        (json.dumps(default_sched),)
                    )
            conn.commit()
    finally:
        if conn:
            conn.close()