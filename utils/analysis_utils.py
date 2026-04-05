"""
analysis_utils.py — Local (zero-API-cost) answer analysis.
Counts words, detects filler words, and computes 4 scores.
"""

import re

FILLER_WORDS = [
    "um", "uh", "like", "basically", "you know", "literally",
    "actually", "right", "so", "well", "kind of", "sort of",
    "i mean", "you see", "okay so", "just", "very", "really"
]

CONFIDENCE_BOOSTERS = [
    "for example", "for instance", "specifically", "the result was",
    "we achieved", "i led", "i built", "i implemented", "i designed",
    "i reduced", "i increased", "i improved", "the outcome", "as a result",
    "in conclusion", "to summarize", "firstly", "secondly", "finally",
    "the impact", "percent", "%", "successfully"
]


def analyze_answer(transcript: str) -> dict:
    """
    Runs purely local analysis on the transcript.
    Returns a dict with scores and detected issues.
    """
    if not transcript or not transcript.strip():
        return _empty_result()

    text = transcript.lower()
    words = re.findall(r"\b\w+\b", transcript)
    word_count = len(words)

    # Filler detection
    detected_fillers = {}
    for filler in FILLER_WORDS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        matches = re.findall(pattern, text)
        if matches:
            detected_fillers[filler] = len(matches)
    total_fillers = sum(detected_fillers.values())

    # Scores (0–100)
    # Clarity: penalise filler %
    filler_ratio = total_fillers / max(word_count, 1)
    clarity = max(0, round(100 - (filler_ratio * 300)))
    clarity = min(clarity, 100)

    # Confidence: reward structured language
    booster_hits = sum(1 for b in CONFIDENCE_BOOSTERS if b in text)
    confidence = min(100, 50 + booster_hits * 7)

    # Length score: optimal 80–220 words
    if 80 <= word_count <= 220:
        length_score = 100
    elif word_count < 80:
        length_score = max(20, round((word_count / 80) * 100))
    else:
        length_score = max(50, round(100 - ((word_count - 220) / 5)))

    # Overall weighted
    overall = round(clarity * 0.35 + confidence * 0.40 + length_score * 0.25)
    overall = max(10, min(100, overall))

    return {
        "word_count": word_count,
        "filler_words": detected_fillers,
        "total_fillers": total_fillers,
        "clarity_score": clarity,
        "confidence_score": confidence,
        "length_score": length_score,
        "overall_score": overall,
    }


def _empty_result() -> dict:
    return {
        "word_count": 0,
        "filler_words": {},
        "total_fillers": 0,
        "clarity_score": 0,
        "confidence_score": 0,
        "length_score": 0,
        "overall_score": 0,
    }


def highlight_fillers(transcript: str) -> str:
    """Returns transcript with filler words wrapped in **bold** markdown."""
    result = transcript
    for filler in sorted(FILLER_WORDS, key=len, reverse=True):
        pattern = r"\b(" + re.escape(filler) + r")\b"
        result = re.sub(pattern, r"**\1**", result, flags=re.IGNORECASE)
    return result
