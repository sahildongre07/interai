"""
pages/2_Interview_Questions.py — AI question bank with filter + practice deep-links.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.llm_utils import generate_question_bank

# ─── Auth guard ────────────────────────────────────────────────────────────────
if "user" not in st.session_state or not st.session_state["user"].get("job_title"):
    st.warning("Please log in and complete your profile first.")
    st.stop()

user = st.session_state["user"]
st.session_state["last_active_page"] = "2_Interview_Questions"

# ─── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Instrument Serif',serif;font-size:36px;line-height:1.1;margin-bottom:4px">
  Question <em style="color:#FF5C3A">bank</em> 📋
</div>
""", unsafe_allow_html=True)

companies_str = " · ".join(user.get("target_companies", [])[:3]) or "top companies"
st.markdown(f"AI-generated questions for **{user.get('job_title','your role')}** at {companies_str}")
st.markdown("---")

# ─── State ─────────────────────────────────────────────────────────────────────
if "question_bank" not in st.session_state:
    st.session_state.question_bank = None
if "qb_filter" not in st.session_state:
    st.session_state.qb_filter = "All"

# ─── Generate button ───────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])
with col1:
    if st.button("🔄 Generate My Question Bank", type="primary", use_container_width=True):
        with st.spinner("🤖 Generating 15 personalised questions..."):
            try:
                bank = generate_question_bank(
                    job_title=user.get("job_title", "Software Engineer"),
                    companies=user.get("target_companies", []),
                    experience=user.get("experience_level", "Fresher"),
                )
                st.session_state.question_bank = bank
                st.session_state.qb_filter = "All"
                st.success(f"✅ Generated {len(bank)} questions!")
            except Exception as e:
                st.error(f"Could not generate questions: {e}")

with col2:
    if st.session_state.question_bank:
        # Export as text
        if st.button("📋 Copy All Questions", use_container_width=True):
            text = "\n\n".join([f"{i+1}. [{q['category']}] {q['question']}" for i, q in enumerate(st.session_state.question_bank)])
            st.code(text)

# ─── Filter pills ──────────────────────────────────────────────────────────────
if st.session_state.question_bank:
    bank = st.session_state.question_bank
    categories = ["All"] + sorted(list(set(q.get("category", "Other") for q in bank)))

    filter_cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with filter_cols[i]:
            count = len(bank) if cat == "All" else len([q for q in bank if q.get("category") == cat])
            label = f"{'✓ ' if st.session_state.qb_filter == cat else ''}{cat} ({count})"
            if st.button(label, key=f"filt_{cat}", use_container_width=True):
                st.session_state.qb_filter = cat
                st.rerun()

    # ─── Table ─────────────────────────────────────────────────────────────────
    filtered = bank if st.session_state.qb_filter == "All" else [
        q for q in bank if q.get("category") == st.session_state.qb_filter
    ]

    st.markdown(f"**Showing {len(filtered)} of {len(bank)} questions**")
    st.markdown("---")

    # Category color mapping
    CAT_COLORS = {
        "Behavioral": ("#F4F0FF", "#8B5CF6"),
        "Technical": ("#EEF4FF", "#3B82F6"),
        "Situational": ("#EDFDF5", "#10B981"),
        "Company-Specific": ("#FFFBEB", "#F59E0B"),
    }
    DIFF_COLORS = {
        "Easy": "#10B981",
        "Medium": "#F59E0B",
        "Hard": "#FF5C3A",
    }
    DIFF_EMOJI = {"Easy": "✅", "Medium": "⚡", "Hard": "🔥"}

    for i, q in enumerate(filtered):
        cat = q.get("category", "Other")
        diff = q.get("difficulty", "Medium")
        cat_bg, cat_color = CAT_COLORS.get(cat, ("#F5F5F5", "#666"))
        diff_color = DIFF_COLORS.get(diff, "#666")
        diff_emoji = DIFF_EMOJI.get(diff, "")

        with st.container():
            col_cat, col_diff, col_q, col_why, col_btn = st.columns([1.2, 0.9, 3, 2, 0.8])

            with col_cat:
                st.markdown(f"""
                <span style="background:{cat_bg};border:1.5px solid #1A1714;border-radius:6px;
                     padding:3px 8px;font-size:11px;font-weight:700;color:{cat_color}">
                  {cat}
                </span>
                """, unsafe_allow_html=True)

            with col_diff:
                st.markdown(f"""
                <span style="font-size:12px;font-weight:700;color:{diff_color}">
                  {diff_emoji} {diff}
                </span>
                """, unsafe_allow_html=True)

            with col_q:
                st.markdown(f"<div style='font-size:13.5px;line-height:1.5;padding-top:2px'>{q.get('question','')}</div>", unsafe_allow_html=True)

            with col_why:
                st.markdown(f"<div style='font-size:12px;color:#9A9088;font-style:italic;padding-top:2px'>{q.get('why_asked','')}</div>", unsafe_allow_html=True)

            with col_btn:
                if st.button("Practice →", key=f"practice_{i}", use_container_width=True):
                    # Fully reset practice page state so the new question loads fresh
                    for _key in ["transcript", "analysis", "ai_feedback", "ai_scores", "current_question"]:
                        st.session_state[_key] = None
                    st.session_state["session_saved"] = False
                    st.session_state["asked_questions"] = st.session_state.get("asked_questions", [])
                    st.session_state["preloaded_question"] = q.get("question", "")
                    st.switch_page("pages/1_Interview_Practice.py")

            st.markdown("<hr style='margin:6px 0;border-color:#EDE9DF'>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:center;font-size:12px;color:#9A9088;margin-top:12px'>
      Generated by Llama 3.3 70B via OpenRouter · Free tier
    </div>
    """, unsafe_allow_html=True)

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#FEFCF7;border:2px dashed #DDD8CE;
         border-radius:20px;margin-top:20px">
      <div style="font-size:48px;margin-bottom:12px">📋</div>
      <div style="font-family:'Instrument Serif',serif;font-size:22px;margin-bottom:8px">No questions yet</div>
      <div style="color:#9A9088;font-size:14px">
        Click "Generate My Question Bank" to get 15 personalised interview questions
      </div>
    </div>
    """, unsafe_allow_html=True)