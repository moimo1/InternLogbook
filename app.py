import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from core.database import get_db_connection, init_db
from core.engine import calculate_intern_hours, get_schedule_for_date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_fallback_key')

try:
    init_db()
except Exception as e:
    print(f"Skipping database schema initialization: {e}")

# -------------------------------------------------------------------------
# GLOBAL SESSION SECURITY INTERCEPTOR
# -------------------------------------------------------------------------
@app.before_request
def check_user_activity_status():
    """
    Executes globally before any endpoint router. Instantly revokes session 
    tokens and clears browser cookies if an administrative action deactivates 
    the current logged-in intern profile.
    """
    exempt_routes = ['log_in', 'register', 'static']
    if request.endpoint in exempt_routes:
        return None

    if 'user_id' in session:
        uid = session['user_id']
        
        with get_db_connection() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT is_active, roles FROM users WHERE id = %s', (uid,))
                user = cursor.fetchone()

        if not user or (user['roles'] == 'intern' and user['is_active'] == 0):
            session.clear()
            flash("Session expired: Your internship period has officially ended or your account has been deactivated.", "danger")
            return redirect(url_for('log_in'))

    return None

# -------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def log_in():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('scan'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with get_db_connection() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                
        if user and user['password'] == password:
            if user['is_active'] == 0 and user['roles'] == 'intern':
                flash('Your internship period has ended.', 'danger')
                return redirect(url_for('log_in'))
                
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['roles']
            
            if user['roles'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('scan'))
            
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO users (username, password, roles, is_active) VALUES (%s, %s, %s, %s)',
                        (username, password, 'intern', 1)
                    )
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('log_in'))
        except Exception:
            flash('Username already exists.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('log_in'))

# -------------------------------------------------------------------------
# INTERN INTERACTION ROUTES
# -------------------------------------------------------------------------
@app.route('/scan')
def scan():
    if 'user_id' not in session:
        flash('Please log in.')
        return redirect(url_for('log_in'))

    user_id = session['user_id']
    username = session['username']

    is_late = False
    now = datetime.now()
    current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:

            cursor.execute('SELECT log_type, timestamp from logs WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1', (user_id,))
            last_log = cursor.fetchone()

            # --- DYNAMIC REFRESH LOOP / RAPID SCAN RATE LIMITER (30 MINUTE WINDOW) ---
            if last_log:
                last_log_time = last_log['timestamp']
                time_delta = (now - last_log_time).total_seconds()
                
                if time_delta < 1800:
                    cursor.execute('SELECT DISTINCT timestamp::date as log_date FROM logs WHERE user_id = %s', (user_id,))
                    distinct_dates = cursor.fetchall()
                    
                    total_credited = sum(calculate_intern_hours(user_id, str(d['log_date']))['credited'] for d in distinct_dates)
                    
                    if last_log['log_type'] == 'IN':
                        sched = get_schedule_for_date(last_log_time)
                        target_date_str = last_log_time.strftime('%Y-%m-%d')
                        office_start = datetime.strptime(f"{target_date_str} {sched['start']}:00", '%Y-%m-%d %H:%M:%S')
                        if last_log_time > office_start:
                            is_late = True

                    return render_template('confirmation.html',
                                           username=username,
                                           log_type=last_log['log_type'],
                                           time=last_log_time.strftime('%Y-%m-%d %I:%M %p'),
                                           is_late=is_late,
                                           total_hours=round(total_credited, 2))

            next_log = 'OUT' if (last_log and last_log['log_type'] == 'IN') else 'IN'

            if next_log == 'IN':
                sched = get_schedule_for_date(now)
                target_date_str = now.strftime('%Y-%m-%d')
                office_start = datetime.strptime(f"{target_date_str} {sched['start']}:00", '%Y-%m-%d %H:%M:%S')
                if now > office_start:
                    is_late = True

            cursor.execute('INSERT INTO logs (user_id, log_type, timestamp) VALUES (%s, %s, %s)',
                           (user_id, next_log, current_time_str))
            conn.commit()

            cursor.execute('SELECT DISTINCT timestamp::date as log_date FROM logs WHERE user_id = %s', (user_id,))
            distinct_dates = cursor.fetchall()

    total_credited = 0.0
    for d in distinct_dates:
        res = calculate_intern_hours(user_id, str(d['log_date']))
        total_credited += res['credited']

    return render_template('confirmation.html',
                           username=username,
                           log_type=next_log,
                           time=now.strftime('%Y-%m-%d %I:%M %p'),
                           is_late=is_late,
                           total_hours=round(total_credited, 2))

# -------------------------------------------------------------------------
# ADMINISTRATIVE DASHBOARD ROUTES
# -------------------------------------------------------------------------
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    selected_user_id = request.args.get('filter_user', '')

    with get_db_connection() as conn:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. Fetch Interns Roster List
            cursor.execute("SELECT id, username, is_active FROM users WHERE roles = 'intern' ORDER BY username ASC")
            interns = cursor.fetchall()

            # 2. Fetch Global Schedule System Settings
            cursor.execute("SELECT value FROM system_settings WHERE key = 'schedule_rules'")
            sched_row = cursor.fetchone()
            sched = json.loads(sched_row['value']) if sched_row else {"MWF": {"start": "08:00", "end": "17:00"}, "TF": {"start": "08:00", "end": "17:00"}}

            # 3. Build comprehensive structured timeline history matching query filters
            query = '''
                SELECT l.user_id, u.username, l.log_type, l.timestamp, l.timestamp::date as log_date 
                FROM logs l
                JOIN users u ON l.user_id = u.id
            '''
            params = []
            if selected_user_id:
                query += ' WHERE l.user_id = %s'
                params.append(int(selected_user_id))
            query += ' ORDER BY l.timestamp DESC'
            
            cursor.execute(query, params)
            raw_logs = cursor.fetchall()

            cursor.execute('SELECT user_id, absence_date FROM excused_absences')
            excused_list = cursor.fetchall()
            excused_map = {(e['user_id'], str(e['absence_date'])): True for e in excused_list}

    formatted_logs = []
    user_balances = {}

    for log in reversed(raw_logs):
        uid = log['user_id']
        date_str = str(log['log_date'])
        
        calc = calculate_intern_hours(uid, date_str)
        
        if uid not in user_balances:
            user_balances[uid] = 0.0
        
        if not any(fl['user_id'] == uid and fl['date_str'] == date_str for fl in formatted_logs):
            user_balances[uid] += calc['credited']

        formatted_logs.append({
            'user_id': uid,
            'username': log['username'],
            'type': log['log_type'],
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %I:%M %p'),
            'date_str': date_str,
            'raw': calc['raw'],
            'credited': calc['credited'],
            'potential_ot': calc['potential_ot'],
            'is_ot_approved': calc['is_ot_approved'],
            'is_excused': excused_map.get((uid, date_str), False),
            'total_overall': round(user_balances[uid], 2)
        })

    formatted_logs.reverse()

    return render_template('admin.html',
                           interns=interns,
                           logs=formatted_logs,
                           sched=sched,
                           selected_user_id=selected_user_id)

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    updated_sched = {
        "MWF": {
            "start": request.form.get('mwf_start'), 
            "end": request.form.get('mwf_end'),
            "break_start": request.form.get('mwf_break_start'),
            "break_end": request.form.get('mwf_break_end')
        },
        "TF":  {
            "start": request.form.get('tf_start'),  
            "end": request.form.get('tf_end'),
            "break_start": request.form.get('tf_break_start'),
            "break_end": request.form.get('tf_break_end')
        }
    }
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO system_settings (key, value) VALUES ('schedule_rules', %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            ''', (json.dumps(updated_sched),))
        conn.commit()
        
    flash("Schedule guidelines updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/intern/toggle/<int:user_id>', methods=['POST'])
def toggle_intern_status(user_id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    status = request.form.get('is_active')
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE users SET is_active = %s WHERE id = %s', (int(status), user_id))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/intern/delete/<int:user_id>', methods=['POST'])
def delete_intern(user_id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logs/manual-insert', methods=['POST'])
def manual_insert_log():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    user_id = request.form.get('user_id')
    log_type = request.form.get('log_type')
    log_date = request.form.get('manual_date')
    log_time = request.form.get('manual_time')
    
    if user_id and log_type and log_date and log_time:
        full_timestamp = f"{log_date} {log_time}:00"
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('INSERT INTO logs (user_id, log_type, timestamp) VALUES (%s, %s, %s)',
                               (int(user_id), log_type, full_timestamp))
            conn.commit()
            
    return redirect(url_for('admin_dashboard', filter_user=user_id))

# -------------------------------------------------------------------------
# ADMINISTRATIVE OVERRIDE PATHWAYS (ABSENCE & OVERTIME)
# -------------------------------------------------------------------------
@app.route('/admin/absence/excuse', methods=['POST'])
def excuse_absence():
    if session.get('role') != 'admin': return "Unauthorized", 403
    user_id = request.form.get('user_id')
    absence_date = request.form.get('absence_date')
    
    if user_id and absence_date:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO excused_absences (user_id, absence_date) VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                ''', (int(user_id), absence_date))
            conn.commit()
    return redirect(url_for('admin_dashboard', filter_user=user_id))

@app.route('/admin/absence/unexcuse', methods=['POST'])
def unexcuse_absence():
    if session.get('role') != 'admin': return "Unauthorized", 403
    user_id = request.form.get('user_id')
    absence_date = request.form.get('absence_date')
    
    if user_id and absence_date:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM excused_absences WHERE user_id = %s AND absence_date = %s',
                               (int(user_id), absence_date))
            conn.commit()
    return redirect(url_for('admin_dashboard', filter_user=user_id))

@app.route('/admin/overtime/approve', methods=['POST'])
def approve_overtime():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    user_id = request.form.get('user_id')
    absence_date = request.form.get('absence_date')
    ot_hours = request.form.get('ot_hours')

    if user_id and absence_date and ot_hours:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO approved_overtime (user_id, overtime_date, hours_approved)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, overtime_date) DO UPDATE 
                    SET hours_approved = EXCLUDED.hours_approved
                ''', (int(user_id), absence_date, float(ot_hours)))
            conn.commit()
    return redirect(url_for('admin_dashboard', filter_user=user_id))

@app.route('/admin/overtime/revoke', methods=['POST'])
def revoke_overtime():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    user_id = request.form.get('user_id')
    absence_date = request.form.get('absence_date')

    if user_id and absence_date:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    DELETE FROM approved_overtime 
                    WHERE user_id = %s AND overtime_date = %s
                ''', (int(user_id), absence_date))
            conn.commit()
    return redirect(url_for('admin_dashboard', filter_user=user_id))