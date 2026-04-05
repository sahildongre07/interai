"""
whisper_utils.py — Audio transcription via Groq's Whisper API.
Uses the whisper-large-v3-turbo model (free tier, fast).
"""

import os
import tempfile
import streamlit as st

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Sends raw audio bytes to Groq Whisper.
    Returns transcribed text string, or raises on failure.
    """
    if not GROQ_AVAILABLE:
        raise RuntimeError("groq package not installed. Run: pip install groq")

    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to .streamlit/secrets.toml or environment variables.")

    client = Groq(api_key=api_key)

    # Write bytes to a temp file — Groq SDK needs a file-like object
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                prompt="Professional technical interview answer. May contain software engineering terms, algorithms, data structures, system design concepts.",
                response_format="text",
                language="en",
            )
        return transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
    finally:
        os.unlink(tmp_path)


def _get_api_key() -> str:
    """Tries st.secrets first, then environment variable."""
    try:
        return st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")
