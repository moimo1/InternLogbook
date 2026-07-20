from datetime import datetime


def get_schedule_for_date(dt_obj):
    """
    Determines whether a given date object falls under MWF or TF office 
    hour thresholds. Reads from system configuration rules.
    """
    import json
    from core.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    weekday = dt_obj.weekday()  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
    sched_key = "MWF" if weekday in [0, 2, 4] else "TF"

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT value FROM system_settings WHERE key = 'schedule_rules'")
            row = cursor.fetchone()

    default_rules = {"start": "08:00", "end": "17:00", "break_start": "12:00", "break_end": "13:00"}
    if row:
        rules = json.loads(row['value'])
        sched = rules.get(sched_key, default_rules)
        # Ensure we have break start and end key fallbacks
        if "break_start" not in sched:
            sched["break_start"] = "12:00"
        if "break_end" not in sched:
            sched["break_end"] = "13:00"
        return sched
    return default_rules


def calculate_intern_hours(user_id, log_date_str, daily_logs=None, ot_approved=None):
    """
    Calculates raw, credited, and overtime hours for a specific intern.
    Cradles a minimum 30-minute requirement for overtime approval eligibility.
    """
    from core.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    target_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()

    if daily_logs is None or ot_approved is None:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if daily_logs is None:
                    # Fetch shift logs matching this distinct date
                    cursor.execute('''
                                   SELECT log_type, timestamp
                                   FROM logs
                                   WHERE user_id = %s
                                     AND timestamp :: date = %s
                                   ORDER BY timestamp ASC
                                   ''', (user_id, target_date))
                    logs = cursor.fetchall()
                else:
                    logs = daily_logs

                if ot_approved is None:
                    # Check if an admin approved overtime for this specific date
                    cursor.execute('''
                                   SELECT hours_approved
                                   FROM approved_overtime
                                   WHERE user_id = %s
                                     AND overtime_date = %s
                                   ''', (user_id, target_date))
                    ot_row = cursor.fetchone()
                    ot_approved = float(ot_row['hours_approved']) if ot_row else 0.0
    else:
        logs = daily_logs

    raw_hours = 0.0
    credited_hours = 0.0
    potential_ot = 0.0

    i = 0
    while i < len(logs):
        if logs[i]['log_type'] == 'IN':
            if i + 1 < len(logs) and logs[i + 1]['log_type'] == 'OUT':
                in_time = logs[i]['timestamp']
                out_time = logs[i + 1]['timestamp']

                # FORGOT TO CLOCK OUT SAFEGUARD: Ensure both stamps are on the same calendar day
                if in_time.date() == out_time.date():
                    shift_duration = (out_time - in_time).total_seconds() / 3600.0
                    raw_hours += shift_duration

                    # Fetch schedule bounds
                    sched = get_schedule_for_date(in_time)
                    office_start = datetime.strptime(f"{log_date_str} {sched['start']}:00", '%Y-%m-%d %H:%M:%S')
                    office_end = datetime.strptime(f"{log_date_str} {sched['end']}:00", '%Y-%m-%d %H:%M:%S')

                    # Base credited window boundaries (bounded inside standard office hours)
                    cred_in = max(in_time, office_start)
                    cred_out = min(out_time, office_end)

                    if cred_out > cred_in:
                        # Calculate lunch break overlap if break config exists
                        break_start_str = sched.get("break_start", "12:00")
                        break_end_str = sched.get("break_end", "13:00")
                        break_start = datetime.strptime(f"{log_date_str} {break_start_str}:00", '%Y-%m-%d %H:%M:%S')
                        break_end = datetime.strptime(f"{log_date_str} {break_end_str}:00", '%Y-%m-%d %H:%M:%S')
                        
                        overlap_start = max(cred_in, break_start)
                        overlap_end = min(cred_out, break_end)
                        overlap_hours = 0.0
                        if overlap_end > overlap_start:
                            overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0
                            
                        credited_hours += ((cred_out - cred_in).total_seconds() / 3600.0) - overlap_hours

                    # --- OVERTIME CALCULATION ---
                    # Check if they clocked out PAST the official office close window
                    if out_time > office_end:
                        ot_duration = (out_time - office_end).total_seconds() / 3600.0

                        # Enforce the minimum 30-minute threshold constraint
                        if ot_duration >= 0.5:
                            potential_ot += ot_duration

                i += 2
            else:
                # Orphaned IN at end of list
                i += 1
        else:
            # Stray OUT log
            i += 1

    # If the admin approved the overtime, credit those hours to the baseline total
    if ot_approved > 0.0:
        credited_hours += ot_approved

    return {
        "raw": round(raw_hours, 2),
        "credited": round(credited_hours, 2),
        "potential_ot": round(potential_ot, 2),
        "is_ot_approved": ot_approved > 0.0
    }