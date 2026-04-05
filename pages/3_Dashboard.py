"""
pages/3_Dashboard.py — Progress analytics dashboard.
Reads session files and renders charts using Plotly.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.storage_utils import get_user_sessions, get_session_stats

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

# ─── Auth guard ────────────────────────────────────────────────────────────────
if "user" not in st.session_state or not st.session_state["user"].get("job_title"):
    st.warning("Please log in and complete your profile first.")
    st.stop()

user = st.session_state["user"]

# ─── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Instrument Serif',serif;font-size:36px;line-height:1.1;margin-bottom:4px">
  Your <em style="color:#FF5C3A">progress</em> 📊
</div>
""", unsafe_allow_html=True)
st.markdown(f"**{user['name']}** · {user.get('job_title','')} · {user.get('experience_level','').split('(')[0].strip()}")
st.markdown("---")

# ─── Load data ─────────────────────────────────────────────────────────────────
sessions = get_user_sessions(user["id"])
stats = get_session_stats(sessions)

if st.button("🔄 Refresh Data"):
    st.rerun()

# ─── Summary metrics ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Total Sessions", stats["total_sessions"],
              f"{stats.get('total_practice',0)} practice · {stats.get('total_coding',0)} coding")
with col2:
    st.metric("📈 Avg Score", f"{stats['avg_overall_score']}/100",
              "↑ Keep going!" if stats["avg_overall_score"] > 0 else None)
with col3:
    st.metric("✨ Avg Clarity", f"{stats['avg_clarity_score']}/100")
with col4:
    st.metric("🏆 Best Score", f"{stats['best_score']}/100",
              "Personal best!" if stats["best_score"] > 0 else None)

st.markdown("---")

# ─── Charts ────────────────────────────────────────────────────────────────────
if not sessions:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#FEFCF7;border:2px dashed #DDD8CE;
         border-radius:20px;margin-top:20px">
      <div style="font-size:48px;margin-bottom:12px">📊</div>
      <div style="font-family:'Instrument Serif',serif;font-size:22px;margin-bottom:8px">No sessions yet</div>
      <div style="color:#9A9088;font-size:14px">Complete a practice or coding session to see your progress here</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if PLOTLY_OK:
    col_chart1, col_chart2 = st.columns([2, 1])

    # Score over time
    with col_chart1:
        st.markdown("#### Score Over Time")
        scores_data = stats.get("scores_over_time", [])
        if scores_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(scores_data) + 1)),
                y=[s["score"] for s in scores_data],
                mode="lines+markers",
                line=dict(color="#B14EFF", width=3),
                marker=dict(size=8, color="#B14EFF", line=dict(width=2, color="#1A1714")),
                fill="tozeroy",
                fillcolor="rgba(177,78,255,0.1)",
                name="Score",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, title="Session"),
                yaxis=dict(showgrid=True, gridcolor="#EDE9DF", range=[0, 105], title="Score"),
                height=260,
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No score data yet.")

    # Category scores
    with col_chart2:
        st.markdown("#### Score by Category")
        cat_scores = stats.get("category_scores", {})
        if cat_scores:
            CAT_COLORS_MAP = {
                "Behavioral": "#8B5CF6",
                "Technical": "#3B82F6",
                "Situational": "#10B981",
                "Company-Specific": "#F59E0B",
                "Coding": "#B14EFF",
                "coding": "#B14EFF",
                "practice": "#FF5C3A",
            }
            colors = [CAT_COLORS_MAP.get(c, "#B14EFF") for c in cat_scores.keys()]
            fig2 = go.Figure(go.Bar(
                x=list(cat_scores.keys()),
                y=list(cat_scores.values()),
                marker=dict(color=colors, line=dict(color="#1A1714", width=2)),
                text=list(cat_scores.values()),
                textposition="outside",
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#EDE9DF", range=[0, 110]),
                height=260,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No category data yet.")

    # Filler words donut
    filler_totals = stats.get("filler_totals", {})
    if filler_totals:
        col_donut, col_donut2 = st.columns([1, 1])
        with col_donut:
            st.markdown("#### Top Filler Words")
            DONUT_COLORS = ["#B14EFF", "#FF5C3A", "#3B82F6", "#F59E0B", "#10B981", "#EC4899", "#8B5CF6", "#14B8A6"]
            fig3 = go.Figure(go.Pie(
                labels=list(filler_totals.keys()),
                values=list(filler_totals.values()),
                hole=0.55,
                marker=dict(colors=DONUT_COLORS[:len(filler_totals)], line=dict(color="#1A1714", width=2)),
                textinfo="label+percent",
                textfont=dict(family="Plus Jakarta Sans", size=12),
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=260,
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True)

else:
    st.warning("Install plotly for charts: `pip install plotly`")
    # Fallback: show table
    st.markdown("#### Scores")
    for s in stats.get("scores_over_time", []):
        st.write(f"Session {s.get('label','')}: {s.get('score','')}/100")

# ─── Recent sessions ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="font-family:'Instrument Serif',serif;font-size:24px;margin-bottom:14px">
  Recent sessions
</div>
""", unsafe_allow_html=True)

recent = sessions[:10]
for s in recent:
    score = s.get("overall_score", 0)
    stype = s.get("type", "practice")
    saved_at = s.get("saved_at", "")[:10]

    if score >= 75:
        score_bg = "#B14EFF"
        score_color = "white"
        verdict = "Strong ✦"
        verdict_color = "#10B981"
    elif score >= 55:
        score_bg = "#FFFBEB"
        score_color = "#92400E"
        verdict = "Average"
        verdict_color = "#F59E0B"
    else:
        score_bg = "#FFF0EC"
        score_color = "#FF5C3A"
        verdict = "Needs Work"
        verdict_color = "#FF5C3A"

    question_preview = s.get("question", s.get("problem_title", "Session"))[:80]
    if stype == "coding":
        question_preview = f"💻 Coding: {question_preview}"
    category = s.get("category", stype.title())
    fillers = s.get("total_fillers", 0)
    filler_str = f" · {fillers} fillers" if stype == "practice" and fillers is not None else ""

    col_score, col_info, col_badge = st.columns([0.6, 4, 1])
    with col_score:
        st.markdown(f"""
        <div style="width:52px;height:52px;border-radius:12px;background:{score_bg};border:2px solid #1A1714;
             display:flex;flex-direction:column;align-items:center;justify-content:center;
             font-family:'Instrument Serif',serif;font-size:22px;line-height:1;color:{score_color};
             box-shadow:2px 2px 0 #1A1714">
          {score}
        </div>
        """, unsafe_allow_html=True)
    with col_info:
        st.markdown(f"""
        <div style="font-size:13.5px;font-weight:600;margin-bottom:2px">{question_preview}{"..." if len(s.get("question","")) > 80 else ""}</div>
        <div style="font-size:11.5px;color:#9A9088">{saved_at} · {category}{filler_str} · 
          <span style="color:{verdict_color};font-weight:700">{verdict}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_badge:
        st.markdown(f"""
        <div style="background:{score_bg};border:2px solid #1A1714;border-radius:20px;padding:4px 12px;
             font-size:12px;font-weight:800;color:{score_color};text-align:center;
             box-shadow:2px 2px 0 #1A1714">
          {score}
        </div>
        """, unsafe_allow_html=True)

    # Expandable feedback
    ai_fb = s.get("ai_feedback", {})
    if ai_fb:
        with st.expander("View AI feedback"):
            well = ai_fb.get("what_went_well", [])
            improve = ai_fb.get("areas_to_improve", [])
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**✅ What went well:**")
                for p in well:
                    st.markdown(f"→ {p}")
            with col_b:
                st.markdown("**⚡ To improve:**")
                for p in improve:
                    st.markdown(f"→ {p}")

    st.markdown("<hr style='margin:8px 0;border-color:#EDE9DF'>", unsafe_allow_html=True)
