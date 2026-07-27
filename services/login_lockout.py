"""
Login lockout tracking: locks an account out for a period of time after too
many failed password attempts. State is persisted to a local JSON file so it
survives app restarts, the same way session_manager.py persists sessions.
"""

import os
import json
import time

LOGIN_LOCKOUT_FILE = os.path.join(os.path.dirname(__file__), "..", ".login_lockout.json")
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60  # 1 minute (60 seconds)


def _load_lockout_data():
    if not os.path.exists(LOGIN_LOCKOUT_FILE):
        return {}
    try:
        with open(LOGIN_LOCKOUT_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_lockout_data(data):
    try:
        with open(LOGIN_LOCKOUT_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_lockout_remaining_seconds(email: str) -> int:
    """Return seconds remaining on an active lockout for this email, or 0 if not locked."""
    if not email:
        return 0
    data = _load_lockout_data()
    entry = data.get(email.strip().lower())
    if not entry or not entry.get("locked_until"):
        return 0
    remaining = entry["locked_until"] - time.time()
    return max(0, int(remaining))


def record_failed_login(email: str):
    """
    Record a failed login attempt for this email.
    Returns (attempts_used, is_locked, lockout_seconds).
    """
    key = email.strip().lower()
    data = _load_lockout_data()
    entry = data.get(key, {"attempts": 0, "locked_until": None})

    # If a previous lockout has already expired, start counting fresh
    if entry.get("locked_until") and entry["locked_until"] <= time.time():
        entry = {"attempts": 0, "locked_until": None}

    entry["attempts"] = entry.get("attempts", 0) + 1
    is_locked = False
    if entry["attempts"] >= MAX_LOGIN_ATTEMPTS:
        entry["locked_until"] = time.time() + LOCKOUT_DURATION_SECONDS
        is_locked = True

    data[key] = entry
    _save_lockout_data(data)
    return entry["attempts"], is_locked, LOCKOUT_DURATION_SECONDS


def reset_login_attempts(email: str):
    if not email:
        return
    key = email.strip().lower()
    data = _load_lockout_data()
    if key in data:
        del data[key]
        _save_lockout_data(data)


def format_lockout_message(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    if minutes > 0:
        return f"Too many failed attempts. Try again in {minutes}m {secs}s."
    return f"Too many failed attempts. Try again in {secs}s."