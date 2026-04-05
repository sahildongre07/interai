"""
auth_utils.py — User authentication, registration, and profile management.
Uses bcrypt for password hashing. Stores user data as JSON files.
"""

import json
import os
import hashlib
import bcrypt
from datetime import datetime

USERS_DIR = "data/users"


def _ensure_dirs():
    os.makedirs(USERS_DIR, exist_ok=True)


def _user_path(email: str) -> str:
    md5 = hashlib.md5(email.lower().encode()).hexdigest()
    return os.path.join(USERS_DIR, f"{md5}.json")


def create_user(name: str, email: str, password: str) -> dict | None:
    """
    Creates a new user. Returns user dict on success, None if email already exists.
    """
    _ensure_dirs()
    path = _user_path(email)
    if os.path.exists(path):
        return None  # already registered

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    user = {
        "id": hashlib.md5(email.lower().encode()).hexdigest(),
        "name": name.strip(),
        "email": email.lower().strip(),
        "password_hash": pw_hash,
        "job_title": "",
        "target_companies": [],
        "experience_level": "",
        "created_at": datetime.now().isoformat(),
    }
    with open(path, "w") as f:
        json.dump(user, f, indent=2)
    return _safe_user(user)


def login_user(email: str, password: str) -> dict | None:
    """
    Validates credentials. Returns user dict (no hash) on success, None on failure.
    """
    _ensure_dirs()
    path = _user_path(email)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        user = json.load(f)
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return _safe_user(user)
    return None


def update_profile(user_id: str, job_title: str, target_companies: list, experience_level: str):
    """Persist updated profile fields for the given user id."""
    _ensure_dirs()
    for fname in os.listdir(USERS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(USERS_DIR, fname)
        with open(fpath) as f:
            user = json.load(f)
        if user.get("id") == user_id:
            user["job_title"] = job_title.strip()
            user["target_companies"] = [c.strip() for c in target_companies if c.strip()]
            user["experience_level"] = experience_level
            with open(fpath, "w") as f:
                json.dump(user, f, indent=2)
            return _safe_user(user)
    return None


def _safe_user(user: dict) -> dict:
    """Returns a copy of user dict without the password hash."""
    return {k: v for k, v in user.items() if k != "password_hash"}
