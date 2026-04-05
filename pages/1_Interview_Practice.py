"""
pages/1_Interview_Practice.py — Voice practice with AI feedback.
6-step flow: question → record → transcribe → analyze → feedback → save.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.auth_utils import *
from utils.llm_utils import generate_question, generate_feedback, score_answer_with_ai
from utils.whisper_utils import transcribe_audio
from utils.analysis_utils import analyze_answer, highlight_fillers
from utils.storage_utils import save_session

# ─── Auth guard ────────────────────────────────────────────────────────────────
if "user" not in st.session_state or not st.session_state["user"].get("job_title"):
    st.warning("Please log in and complete your profile first.")
    st.stop()

user = st.session_state["user"]

# ─── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Instrument Serif',serif;font-size:36px;line-height:1.1;margin-bottom:4px">
  Let's <em style="color:#FF5C3A">practice</em> 🎙️
</div>
""", unsafe_allow_html=True)
companies_str = " · ".join(user.get("target_companies", [])[:3]) or "top companies"
st.markdown(f"Preparing for **{user.get('job_title','your role')}** at {companies_str}", unsafe_allow_html=False)
st.markdown("---")

# ─── Session state init ────────────────────────────────────────────────────────
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "ai_feedback" not in st.session_state:
    st.session_state.ai_feedback = None
if "ai_scores" not in st.session_state:
    st.session_state.ai_scores = None
if "session_saved" not in st.session_state:
    st.session_state.session_saved = False
if "preloaded_question" not in st.session_state:
    st.session_state.preloaded_question = None

# ─── Auto-reset when navigating back from another page ─────────────────────────
# If the user left this page (last_active_page was something else) and has now
# returned, clear the previous answer so they start fresh.
_current_page = "interview_practice"
_last_page = st.session_state.get("last_active_page", _current_page)
if _last_page != _current_page:
    # Came from a different page — reset answer state (keep asked_questions history)
    st.session_state.transcript = None
    st.session_state.analysis = None
    st.session_state.ai_feedback = None
    st.session_state.ai_scores = None
    st.session_state.session_saved = False
    # Only reset current_question if no preloaded_question is waiting
    if not st.session_state.get("preloaded_question"):
        st.session_state.current_question = None
st.session_state["last_active_page"] = _current_page

# ─── Step 1: Load/show question ────────────────────────────────────────────────
col_q, col_btn = st.columns([4, 1])

with col_btn:
    if st.button("🔁 New Question", use_container_width=True):
        st.session_state.current_question = None
        st.session_state.transcript = None
        st.session_state.analysis = None
        st.session_state.ai_feedback = None
        st.session_state.ai_scores = None
        st.session_state.session_saved = False
        st.session_state.preloaded_question = None

# Check for pre-loaded question from Question Bank
if st.session_state.preloaded_question:
    st.session_state.current_question = st.session_state.preloaded_question
    st.session_state.preloaded_question = None

if st.session_state.current_question is None:
    with st.spinner("🤖 Generating your personalised question..."):
        try:
            q = generate_question(
                job_title=user.get("job_title", "Software Engineer"),
                companies=user.get("target_companies", []),
                experience=user.get("experience_level", "Fresher"),
                asked_before=st.session_state.asked_questions[-10:],
            )
            st.session_state.current_question = q
            st.session_state.asked_questions.append(q)
            st.session_state.transcript = None
            st.session_state.analysis = None
            st.session_state.ai_feedback = None
            st.session_state.session_saved = False
        except Exception as e:
            st.error(f"Could not generate question: {e}")
            st.session_state.current_question = "Tell me about a challenging project you worked on. How did you approach problem-solving, and what was the outcome?"

question = st.session_state.current_question

# Display question card
st.markdown(f"""
<div class="question-card">
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
    <span style="background:rgba(0,0,0,.12);border:1.5px solid rgba(0,0,0,.2);border-radius:20px;
         padding:3px 12px;font-size:11px;font-weight:700">🏢 {(user.get('target_companies') or ['Company'])[0]}</span>
    <span style="background:rgba(255,255,255,.3);border:1.5px solid rgba(255,255,255,.5);border-radius:20px;
         padding:3px 12px;font-size:11px;font-weight:700;color:#1A1714">Interview Question</span>
  </div>
  <div style="font-family:'Instrument Serif',serif;font-size:22px;line-height:1.5;color:#1A1714;
       position:relative;z-index:1">
    {question}
  </div>
  <div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap">
    <span style="background:rgba(0,0,0,.08);border:1px solid rgba(0,0,0,.12);border-radius:6px;
         padding:3px 10px;font-size:11.5px;font-weight:600">💡 Use STAR method</span>
    <span style="background:rgba(0,0,0,.08);border:1px solid rgba(0,0,0,.12);border-radius:6px;
         padding:3px 10px;font-size:11.5px;font-weight:600">🎯 Aim for 90–180 words</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Step 2 & 3: Record audio ──────────────────────────────────────────────────
st.markdown("### 🎙️ Record Your Answer")
st.info("💡 Click the microphone button below to record your answer. Click again to stop.")

try:
    from audio_recorder_streamlit import audio_recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#FF5C3A",
        neutral_color="#B14EFF",
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=3.0,
        sample_rate=16000,
    )
except ImportError:
    st.warning("audio-recorder-streamlit not installed. Using file upload as fallback.")
    audio_bytes = None

# File upload fallback
st.markdown("**Or upload an audio file:**")
uploaded_file = st.file_uploader("Upload audio (MP3, WAV, WebM, M4A)", type=["mp3", "wav", "webm", "m4a"], label_visibility="collapsed")
if uploaded_file:
    audio_bytes = uploaded_file.read()

# ─── Step 3: Transcribe ────────────────────────────────────────────────────────
if audio_bytes and len(audio_bytes) > 1000:
    if st.session_state.transcript is None:
        col_analyze, col_skip = st.columns([2, 1])
        with col_analyze:
            if st.button("📤 Transcribe & Analyze My Answer", use_container_width=True, type="primary"):
                with st.spinner("🎧 Transcribing your answer with Groq Whisper..."):
                    try:
                        transcript = transcribe_audio(audio_bytes)
                        st.session_state.transcript = transcript
                        st.success("✅ Transcription complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
                        st.info("💡 Tip: Make sure GROQ_API_KEY is set in .streamlit/secrets.toml")
        with col_skip:
            manual_transcript = st.text_area("Or type your answer manually:", height=100, placeholder="Paste or type your answer here...")
            if st.button("Use typed answer →"):
                if manual_transcript.strip():
                    st.session_state.transcript = manual_transcript.strip()
                    st.rerun()

# Manual transcript input (always available)
if st.session_state.transcript is None and (not audio_bytes or len(audio_bytes) <= 1000):
    st.markdown("**Don't have a mic? Type your answer:**")
    manual_transcript = st.text_area("Your answer:", height=150, placeholder="Type your answer here and we'll analyze it...")
    if st.button("📊 Analyze typed answer →", type="primary"):
        if manual_transcript.strip():
            st.session_state.transcript = manual_transcript.strip()
            st.rerun()
        else:
            st.error("Please enter your answer first.")

# ─── Steps 4 & 5: Analyze + AI Feedback ───────────────────────────────────────
if st.session_state.transcript:
    transcript = st.session_state.transcript

    # Step 4: Local analysis (filler words, word count — always instant)
    if st.session_state.analysis is None:
        st.session_state.analysis = analyze_answer(transcript)

    analysis = st.session_state.analysis

    st.markdown("---")
    st.markdown("### 📝 Your Answer")

    # Show transcript with filler highlights
    highlighted = highlight_fillers(transcript)
    st.markdown(f"""
    <div style="background:#EDE9DF;border:2px solid #DDD8CE;border-radius:12px;
         padding:16px;font-size:13.5px;line-height:1.7;color:#4A4540;margin-bottom:18px">
      {highlighted.replace('**', '<mark style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:4px;padding:0 3px;font-weight:700;font-size:12px">').replace('**', '</mark>')}
    </div>
    """, unsafe_allow_html=True)

    # ── AI Scoring ──────────────────────────────────────────────────────────
    if st.session_state.ai_scores is None:
        with st.spinner("🤖 Scoring your answer with AI..."):
            try:
                ai_scores = score_answer_with_ai(question, transcript, analysis)
                st.session_state.ai_scores = ai_scores
            except Exception as e:
                # Fallback to local scores silently
                st.session_state.ai_scores = {
                    "overall_score": analysis["overall_score"],
                    "clarity_score": analysis["clarity_score"],
                    "confidence_score": analysis["confidence_score"],
                    "relevance_score": 50,
                    "structure_score": 50,
                    "score_reasoning": "AI scoring unavailable — showing estimated scores.",
                }

    scores = st.session_state.ai_scores

    # Score metrics
    st.markdown("### 📊 Your Scores")
    st.markdown(
        f"""<div style="background:#F0FDF4;border:1.5px solid #86EFAC;border-radius:10px;
             padding:10px 16px;font-size:13px;color:#166534;margin-bottom:14px">
          🤖 <strong>AI-evaluated</strong> — {scores.get('score_reasoning', '')}
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        score = scores["overall_score"]
        delta_label = "Strong ✦" if score >= 75 else ("Average" if score >= 55 else "Needs Work")
        st.metric("🏆 Overall", f"{score}/100", delta_label)
        st.progress(score / 100)
    with col2:
        st.metric("✨ Clarity", f"{scores['clarity_score']}/100",
                  f"{analysis['total_fillers']} fillers" if analysis['total_fillers'] > 0 else "Clean!")
        st.progress(scores["clarity_score"] / 100)
    with col3:
        st.metric("💪 Confidence", f"{scores['confidence_score']}/100")
        st.progress(scores["confidence_score"] / 100)
    with col4:
        st.metric("🎯 Relevance", f"{scores['relevance_score']}/100")
        st.progress(scores["relevance_score"] / 100)
    with col5:
        st.metric("🗂️ Structure", f"{scores['structure_score']}/100")
        st.progress(scores["structure_score"] / 100)

    # Word count info row
    wc = analysis["word_count"]
    wc_label = "✅ Ideal range" if 80 <= wc <= 220 else ("⚠️ Too short" if wc < 80 else "⚠️ Too long")
    st.markdown(
        f"""<div style="background:#EDE9DF;border:1px solid #DDD8CE;border-radius:8px;
             padding:8px 14px;font-size:13px;color:#4A4540;margin-top:6px">
          📏 <strong>Word count:</strong> {wc} words — {wc_label} (aim for 80–220)
        </div>""",
        unsafe_allow_html=True,
    )

    # Filler word breakdown
    if analysis["filler_words"]:
        with st.expander(f"⚠️ Filler Words Detected ({analysis['total_fillers']} total)"):
            for word, count in sorted(analysis["filler_words"].items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- **{word}** → {count}x")

    # Step 5: AI Feedback
    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <span style="font-family:'Instrument Serif',serif;font-size:24px">🤖 AI Feedback</span>
      <span style="font-size:11.5px;color:#9A9088;background:#EDE9DF;border:1.5px solid #DDD8CE;
           padding:2px 10px;border-radius:20px;font-weight:600">Llama 3.3 70B · free</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.ai_feedback is None:
        if st.button("🤖 Get AI Feedback", use_container_width=True, type="primary"):
            with st.spinner("🧠 Analysing your answer with AI..."):
                try:
                    fb = generate_feedback(question, transcript, scores)
                    st.session_state.ai_feedback = fb
                    st.rerun()
                except Exception as e:
                    st.error(f"AI feedback failed: {e}")
                    st.info("Check your OPENROUTER_API_KEY in .streamlit/secrets.toml")

    if st.session_state.ai_feedback:
        fb = st.session_state.ai_feedback

        col_good, col_warn = st.columns(2)
        with col_good:
            st.markdown("""<div class="feedback-good">""", unsafe_allow_html=True)
            st.markdown("**✅ What went well**")
            for point in fb.get("what_went_well", []):
                st.markdown(f"→ {point}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_warn:
            st.markdown("""<div class="feedback-warn">""", unsafe_allow_html=True)
            st.markdown("**⚡ Areas to improve**")
            for point in fb.get("areas_to_improve", []):
                st.markdown(f"→ {point}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="feedback-ideal">""", unsafe_allow_html=True)
        st.markdown("**💡 Ideal Answer Structure**")
        for step in fb.get("ideal_answer_structure", []):
            st.markdown(f"→ {step}")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("📝 Example Strong Answer"):
            st.info(fb.get("example_strong_answer", ""))

        if fb.get("filler_word_advice"):
            st.markdown(f"""
            <div style="background:#FFF7ED;border:2px solid #F59E0B;border-radius:12px;
                 padding:12px 16px;margin-top:12px;font-size:13.5px;color:#92400E;font-weight:500">
              🗣️ {fb['filler_word_advice']}
            </div>
            """, unsafe_allow_html=True)

        # Step 6: Save session
        if not st.session_state.session_saved:
            session_data = {
                "type": "practice",
                "question": question,
                "transcript": transcript,
                "overall_score": scores["overall_score"],
                "clarity_score": scores["clarity_score"],
                "confidence_score": scores["confidence_score"],
                "relevance_score": scores.get("relevance_score", 50),
                "structure_score": scores.get("structure_score", 50),
                "word_count": analysis["word_count"],
                "filler_words": analysis["filler_words"],
                "total_fillers": analysis["total_fillers"],
                "ai_feedback": fb,
                "category": "Behavioral",
            }
            try:
                save_session(user["id"], session_data)
                st.session_state.session_saved = True
            except Exception:
                pass

        if st.session_state.session_saved:
            st.markdown("""
            <div class="save-success">✅ Session saved to your Dashboard!</div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Practice New Question", use_container_width=True):
                st.session_state.current_question = None
                st.session_state.transcript = None
                st.session_state.analysis = None
                st.session_state.ai_feedback = None
                st.session_state.ai_scores = None
                st.session_state.session_saved = False
                st.rerun()
        with col2:
            if st.button("📊 View Dashboard →", use_container_width=True):
                st.switch_page("pages/3_Dashboard.py")