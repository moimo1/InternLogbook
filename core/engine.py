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

    if row:
        rules = json.loads(row['value'])
        return rules.get(sched_key, {"start": "08:00", "end": "17:00"})
    return {"start": "08:00", "end": "17:00"}


def calculate_intern_hours(user_id, log_date_str):
    """
    Calculates raw, credited, and overtime hours for a specific intern.
    Cradles a minimum 30-minute requirement for overtime approval eligibility.
    """
    from core.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    target_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch shift logs matching this distinct date
            cursor.execute('''
                           SELECT log_type, timestamp
                           FROM logs
                           WHERE user_id = %s
                             AND timestamp :: date = %s
                           ORDER BY timestamp ASC
                           ''', (user_id, target_date))
            logs = cursor.fetchall()

            # Check if an admin approved overtime for this specific date
            cursor.execute('''
                           SELECT hours_approved
                           FROM approved_overtime
                           WHERE user_id = %s
                             AND overtime_date = %s
                           ''', (user_id, target_date))
            ot_row = cursor.fetchone()
            ot_approved = float(ot_row['hours_approved']) if ot_row else 0.0

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
                        credited_hours += (cred_out - cred_in).total_seconds() / 3600.0

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