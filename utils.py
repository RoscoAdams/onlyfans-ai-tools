import json
import os

SCHEDULE_FOLDER = "data/schedules"


def _get_user_schedule_path(email):
    """Converts email to a safe filename."""
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(SCHEDULE_FOLDER, f"{safe_email}.json")


def load_schedule(email):
    path = _get_user_schedule_path(email)
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # fallback if file is empty or broken
    return []


def save_schedule(email, schedule):
    os.makedirs(SCHEDULE_FOLDER, exist_ok=True)  # make sure folder exists
    path = _get_user_schedule_path(email)
    with open(path, "w") as f:
        json.dump(schedule, f, indent=2)
