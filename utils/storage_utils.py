"""
storage_utils.py — Save and load session JSON files.
Sessions are stored in data/sessions/{user_id}_{timestamp}.json
"""

import json
import os
from datetime import datetime

SESSIONS_DIR = "data/sessions"


def _ensure_dirs():
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def save_session(user_id: str, session_data: dict) -> str:
    """Saves a session and returns the file path."""
    _ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{user_id}_{ts}.json"
    fpath = os.path.join(SESSIONS_DIR, fname)
    session_data["saved_at"] = datetime.now().isoformat()
    session_data["user_id"] = user_id
    with open(fpath, "w") as f:
        json.dump(session_data, f, indent=2)
    return fpath


def get_user_sessions(user_id: str) -> list:
    """Returns all sessions for the user, sorted newest first."""
    _ensure_dirs()
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if not fname.startswith(user_id) or not fname.endswith(".json"):
            continue
        fpath = os.path.join(SESSIONS_DIR, fname)
        try:
            with open(fpath) as f:
                sessions.append(json.load(f))
        except Exception:
            continue
    sessions.sort(key=lambda s: s.get("saved_at", ""), reverse=True)
    return sessions


def get_session_stats(sessions: list) -> dict:
    """Computes aggregate stats from a list of session dicts."""
    if not sessions:
        return {
            "total_sessions": 0,
            "avg_overall_score": 0,
            "avg_clarity_score": 0,
            "best_score": 0,
            "scores_over_time": [],
            "category_scores": {},
            "filler_totals": {},
        }

    overall_scores = [s.get("overall_score", 0) for s in sessions if s.get("overall_score")]
    clarity_scores = [s.get("clarity_score", 0) for s in sessions if s.get("clarity_score") and s.get("type") == "practice"]

    # Scores over time (chronological order)
    scores_over_time = []
    for s in reversed(sessions):
        if s.get("overall_score"):
            scores_over_time.append({
                "label": s.get("saved_at", "")[:10],
                "score": s.get("overall_score", 0),
                "type": s.get("type", "practice"),
            })

    # Category scores
    category_map = {}
    for s in sessions:
        cat = s.get("category", s.get("type", "practice"))
        if cat == "coding":
            cat = "Coding"
        score = s.get("overall_score", 0)
        if score:
            if cat not in category_map:
                category_map[cat] = []
            category_map[cat].append(score)
    category_scores = {cat: round(sum(v) / len(v)) for cat, v in category_map.items()}

    # Filler word totals
    filler_totals = {}
    for s in sessions:
        for word, count in s.get("filler_words", {}).items():
            filler_totals[word] = filler_totals.get(word, 0) + count

    practice_sessions = [s for s in sessions if s.get("type") == "practice"]

    return {
        "total_sessions": len(sessions),
        "avg_overall_score": round(sum(overall_scores) / len(overall_scores)) if overall_scores else 0,
        "avg_clarity_score": round(sum(clarity_scores) / len(clarity_scores)) if clarity_scores else 0,
        "best_score": max(overall_scores) if overall_scores else 0,
        "scores_over_time": scores_over_time,
        "category_scores": category_scores,
        "filler_totals": dict(sorted(filler_totals.items(), key=lambda x: x[1], reverse=True)[:8]),
        "total_practice": len(practice_sessions),
        "total_coding": len([s for s in sessions if s.get("type") == "coding"]),
    }
