import os
import csv
from datetime import datetime

ATTENDANCE_FOLDER = "attendance_logs"


def today_file():
    """
    Returns path of today's attendance CSV file
    Example: attendance_logs/attendance_2026-01-15.csv
    """
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
    return os.path.join(ATTENDANCE_FOLDER, f"attendance_{today}.csv")


def ensure_today_file():
    """
    Creates today's file with headers if not exists
    """
    file_path = today_file()

    if not os.path.exists(file_path):
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Time"])

    return file_path


def mark_attendance(name):
    """
    Marks attendance only once per day for each user.
    Returns True if newly marked, False if already marked.
    """
    file_path = ensure_today_file()

    now_time = datetime.now().strftime("%H:%M:%S")

    # Read existing names
    existing_names = set()
    with open(file_path, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) > 0:
                existing_names.add(row[0])

    # If already marked
    if name in existing_names:
        return False

    # Add new entry
    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, now_time])

    return True
