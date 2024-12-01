import requests
from datetime import datetime

def calculate_duration(start_date, start_time, finish_date, finish_time):
    start_datetime_str = f"{start_date} {start_time}"
    finish_datetime_str = f"{finish_date} {finish_time}"

    start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
    finish_datetime = datetime.strptime(finish_datetime_str, "%Y-%m-%d %H:%M")

    duration = finish_datetime - start_datetime

    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return days, hours, minutes


def is_time_conflicting(start_date, start_time, end_date, end_time, other_start_date, other_start_time, other_end_date,
                        other_end_time):
    event_start = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    event_end = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    other_event_start = datetime.strptime(f"{other_start_date} {other_start_time}", "%Y-%m-%d %H:%M")
    other_event_end = datetime.strptime(f"{other_end_date} {other_end_time}", "%Y-%m-%d %H:%M")

    if event_start < other_event_end and event_end > other_event_start:
        return True
    return False
