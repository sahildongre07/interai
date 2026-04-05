"""
app.py — Entry gate for InterviewCoach AI.
Login UI matches the provided HTML reference exactly (split panel).
Home cards are clickable and navigate to pages via st.switch_page.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.auth_utils import create_user, login_user, update_profile

st.set_page_config(
    page_title="InterviewCoach AI ✦",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg: #F5F2EB;
  --bg2: #EDE9DF;
  --white: #FEFCF7;
  --ink: #1A1714;
  --ink2: #4A4540;
  --muted: #9A9088;
  --lime: #B14EFF;
  --lime-dark: #8B2ECC;
  --coral: #FF5C3A;
  --border: #DDD8CE;
  --mint: #10B981;
  --amber: #F59E0B;
  --sky: #3B82F6;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  background: var(--bg) !important;
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── BLOBS ── */
.blob {
  position: fixed; border-radius: 50%; filter: blur(60px);
  pointer-events: none; z-index: 0;
}
.blob-1 { width:420px; height:420px; background:#B14EFF; opacity:.22; top:-100px; right:-80px; }
.blob-2 { width:320px; height:320px; background:#FF5C3A; opacity:.15; bottom:-60px; left:-60px; }
.blob-3 { width:220px; height:220px; background:#3B82F6; opacity:.1; top:40%; left:30%; }

/* ── LOGIN SPLIT PANEL ── */
.login-outer {
  display: flex; align-items: center; justify-content: center;
  min-height: 90vh; padding: 24px;
}
.login-wrap {
  display: grid; grid-template-columns: 1fr 1fr;
  background: var(--white); border: 2px solid var(--ink);
  border-radius: 24px; box-shadow: 0 4px 0 var(--ink);
  overflow: hidden; width: 860px; max-width: 100%;
  position: relative; z-index: 1;
  animation: popIn .5s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes popIn {
  from { opacity:0; transform:scale(.92) translateY(20px); }
  to   { opacity:1; transform:scale(1) translateY(0); }
}
.login-left {
  background: #B14EFF; padding: 48px 40px;
  display: flex; flex-direction: column; justify-content: space-between;
  position: relative; overflow: hidden;
}
.login-left::before {
  content: '✦'; position: absolute; top:-20px; right:-20px;
  font-size: 160px; color: rgba(0,0,0,.06); line-height:1; pointer-events:none;
}
.ll-tag {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--ink); color: #B14EFF; border-radius: 20px;
  padding: 5px 12px; font-size: 11px; font-weight: 700;
  letter-spacing: .06em; text-transform: uppercase; width: fit-content;
}
.ll-heading {
  font-family: 'Instrument Serif', serif; font-size: 44px;
  line-height: 1.1; color: var(--ink); margin-top: 24px;
}
.ll-heading em { font-style: italic; }
.ll-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.ll-pill {
  background: rgba(0,0,0,.1); border: 1.5px solid rgba(0,0,0,.15);
  border-radius: 20px; padding: 5px 12px; font-size: 12px;
  font-weight: 600; color: var(--ink);
}
.ll-foot { font-size: 12px; color: rgba(26,23,20,.55); margin-top: 32px; }
.login-right { padding: 48px 40px; background: var(--white); }
.lr-header { margin-bottom: 28px; }
.lr-header h2 {
  font-family: 'Instrument Serif', serif; font-size: 28px;
  font-weight: 400; color: var(--ink);
}
.lr-header p { color: var(--muted); font-size: 13.5px; margin-top: 4px; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: var(--white) !important;
  border-right: 2px solid var(--ink) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.2rem; }

/* ── BUTTONS ── */
.stButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important; border-radius: 10px !important;
  border: 2px solid var(--ink) !important;
  transition: all .15s !important; box-shadow: 2px 2px 0 var(--ink) !important;
}
.stButton > button:hover {
  transform: translate(-2px,-2px) !important;
  box-shadow: 4px 4px 0 var(--ink) !important;
}
.stButton > button[kind="primary"] {
  background: var(--ink) !important; color: #B14EFF !important;
}

/* ── HOME NAV BUTTONS ── */
div[data-testid="column"] .stButton > button {
  background: var(--white) !important; color: var(--ink) !important;
  font-size: 13px !important; padding: 10px 12px !important;
}
div[data-testid="column"] .stButton > button:hover {
  background: #B14EFF !important; color: white !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  border: 2px solid var(--border) !important; border-radius: 10px !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important; background: var(--bg) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--ink) !important; box-shadow: 3px 3px 0 var(--ink) !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
  background: var(--white); border: 2px solid var(--ink);
  border-radius: 16px; padding: 16px; box-shadow: 3px 3px 0 var(--ink);
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg2) !important; border-radius: 12px !important;
  padding: 4px !important; border: 1.5px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important;
  border-radius: 8px !important;
}
.stTabs [aria-selected="true"] { background: #B14EFF !important; color: white !important; }

/* ── PROGRESS ── */
.stProgress > div > div > div { background: #B14EFF !important; }

/* ── SHARED CARDS ── */
.feedback-good {
  background: #EDFDF5; border: 2px solid #1A1714;
  border-radius: 14px; padding: 20px; box-shadow: 3px 3px 0 #1A1714;
}
.feedback-warn {
  background: #FFFBEB; border: 2px solid #1A1714;
  border-radius: 14px; padding: 20px; box-shadow: 3px 3px 0 #1A1714;
}
.feedback-ideal {
  background: #EEF4FF; border: 2px solid #1A1714;
  border-radius: 14px; padding: 20px; box-shadow: 3px 3px 0 #1A1714;
}
.save-success {
  background: #EDFDF5; border: 2px solid #10B981; border-radius: 12px;
  padding: 14px 18px; box-shadow: 2px 2px 0 #10B981;
  font-weight: 600; color: #065F46;
}

@media(max-width:700px){
  .login-wrap { grid-template-columns:1fr; }
  .login-left { display:none; }
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# LOGIN SCREEN
# ──────────────────────────────────────────────
def show_login():
    # Background blobs
    st.markdown("""
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    """, unsafe_allow_html=True)

    # Left panel HTML
    st.markdown("""
    <div class="login-outer">
      <div class="login-wrap">
        <div class="login-left">
          <div>
            <div class="ll-tag">✦ Free Forever</div>
            <div class="ll-heading">Ace your next <em>interview</em> with AI.</div>
            <div class="ll-pills">
              <span class="ll-pill">🎙️ Voice Practice</span>
              <span class="ll-pill">🤖 AI Feedback</span>
              <span class="ll-pill">📊 Progress Tracker</span>
              <span class="ll-pill">💬 Real Questions</span>
              <span class="ll-pill">💻 Coding Round</span>
            </div>
          </div>
          <div class="ll-foot">No credit card · Free Groq &amp; OpenRouter APIs · Works in browser</div>
        </div>
        <div class="login-right">
          <div class="lr-header">
            <h2>Welcome back ✦</h2>
            <p>Pick up where you left off.</p>
          </div>
    """, unsafe_allow_html=True)

    # Streamlit tabs inside right panel
    tab_login, tab_signup = st.tabs(["🔐 Log In", "✨ Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Log in →", use_container_width=True, type="primary")
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = login_user(email, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="Ramesh Kumar")
            email_s = st.text_input("Email", placeholder="you@example.com")
            password_s = st.text_input("Password", type="password", placeholder="min 6 characters")
            submitted_s = st.form_submit_button("Create free account →", use_container_width=True, type="primary")
            if submitted_s:
                if not name or not email_s or not password_s:
                    st.error("Please fill in all fields.")
                elif len(password_s) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user = create_user(name, email_s, password_s)
                    if user is None:
                        st.error("Email already registered. Please log in.")
                    else:
                        st.session_state["user"] = user
                        st.rerun()

    st.markdown("</div></div></div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# PROFILE SETUP
# ──────────────────────────────────────────────
def show_profile_setup():
    user = st.session_state["user"]
    st.markdown(f"""
    <div style="font-family:'Instrument Serif',serif;font-size:32px;margin-bottom:4px">
        Welcome, <em>{user['name'].split()[0]}</em>! 👋
    </div>
    <div style="color:#9A9088;font-size:14px;margin-bottom:28px">
        Let's personalise your experience before we start.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("profile_form"):
            job_title = st.text_input("Target Job Title", placeholder="e.g. Software Engineer")
            companies_raw = st.text_input(
                "Target Companies (comma-separated)", placeholder="e.g. Google, Amazon, Microsoft"
            )
            experience = st.selectbox("Experience Level", [
                "Fresher (0–1 year)", "Junior (1–3 years)",
                "Mid-level (3–6 years)", "Senior (6+ years)"
            ])
            submitted = st.form_submit_button("Start Practicing →", use_container_width=True, type="primary")
            if submitted:
                if not job_title:
                    st.error("Please enter your target job title.")
                else:
                    companies = [c.strip() for c in companies_raw.split(",") if c.strip()]
                    updated = update_profile(user["id"], job_title, companies, experience)
                    if updated:
                        st.session_state["user"] = updated
                        st.rerun()


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
def show_sidebar():
    user = st.session_state["user"]
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;padding:0 8px 16px;
             font-family:'Instrument Serif',serif;font-size:20px">
          <div style="width:32px;height:32px;border-radius:8px;background:#B14EFF;border:2px solid #1A1714;
               display:flex;align-items:center;justify-content:center;font-size:15px;
               box-shadow:2px 2px 0 #1A1714">🎙</div>
          InterviewCoach
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # User avatar + info
        st.markdown(f"""
        <div style="text-align:center;padding:8px 0 16px">
          <div style="width:52px;height:52px;border-radius:50%;background:#FF5C3A;border:2px solid #1A1714;
               display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;
               color:white;margin:0 auto 8px;box-shadow:2px 2px 0 #1A1714">
               {user['name'][0].upper()}
          </div>
          <div style="font-weight:700;font-size:14px">{user['name']}</div>
          <div style="color:#9A9088;font-size:11px">{user['email']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("**🎯 Profile**")
        st.caption(f"**Role:** {user.get('job_title', 'Not set')}")
        companies = user.get("target_companies", [])
        st.caption(f"**Companies:** {', '.join(companies[:2]) if companies else 'Not set'}")
        st.caption(f"**Level:** {user.get('experience_level', 'Not set')}")

        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile"):
                new_title = st.text_input("Job Title", value=user.get("job_title", ""))
                new_companies = st.text_input("Companies", value=", ".join(user.get("target_companies", [])))
                exp_opts = ["Fresher (0–1 year)", "Junior (1–3 years)", "Mid-level (3–6 years)", "Senior (6+ years)"]
                cur_exp = user.get("experience_level", exp_opts[0])
                new_exp = st.selectbox("Experience", exp_opts,
                    index=exp_opts.index(cur_exp) if cur_exp in exp_opts else 0)
                if st.form_submit_button("Save Changes", use_container_width=True):
                    cos = [c.strip() for c in new_companies.split(",") if c.strip()]
                    updated = update_profile(user["id"], new_title, cos, new_exp)
                    if updated:
                        st.session_state["user"] = updated
                        st.success("Saved!")
                        st.rerun()

        st.divider()
        if st.button("🚪 Log out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:20px;font-size:11px;color:#9A9088;line-height:1.5">
          Free forever<br>Groq Whisper · OpenRouter LLM
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HOME SCREEN  (with clickable cards)
# ──────────────────────────────────────────────
def show_home():
    user = st.session_state["user"]
    name_first = user["name"].split()[0]
    companies = user.get("target_companies", [])
    companies_str = " · ".join(companies[:3]) if companies else "top companies"
    exp = user.get("experience_level", "").split("(")[0].strip()

    # Hero banner — exact style from reference
    st.markdown(f"""
    <div style="background:#B14EFF;border:2px solid #1A1714;border-radius:20px;
         padding:28px 32px;box-shadow:4px 4px 0 #1A1714;margin-bottom:24px;
         position:relative;overflow:hidden">
      <div style="position:absolute;right:24px;top:10px;font-size:120px;color:rgba(0,0,0,.07);
           font-family:'Instrument Serif',serif;line-height:1;pointer-events:none">✦</div>
      <div style="font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;
           color:rgba(255,255,255,.7);margin-bottom:10px">✦ WELCOME BACK</div>
      <div style="font-family:'Instrument Serif',serif;font-size:38px;line-height:1.15;
           color:white;margin-bottom:8px">
        Ready to practice, <em style="font-style:italic">{name_first}</em>?
      </div>
      <div style="color:rgba(255,255,255,.8);font-size:14px;font-weight:500">
        {user.get('job_title','Interview')} prep · {companies_str} · {exp}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:14px;color:#4A4540;margin-bottom:18px">
      👈 Use the <strong>sidebar navigation</strong> — or click a card below to jump straight in.
    </div>
    """, unsafe_allow_html=True)

    # 4 clickable nav cards
    col1, col2, col3, col4 = st.columns(4)
    nav_items = [
        (col1, "🎙️", "Practice", "Voice → AI Feedback", "pages/1_Interview_Practice.py"),
        (col2, "📋", "Questions", "AI Question Bank",    "pages/2_Interview_Questions.py"),
        (col3, "💻", "Coding",    "Problems + Review",   "pages/4_Coding_Round.py"),
        (col4, "📊", "Dashboard", "Progress + Charts",   "pages/3_Dashboard.py"),
    ]
    for col, icon, title, subtitle, page in nav_items:
        with col:
            # Card visual
            st.markdown(f"""
            <div style="background:#FEFCF7;border:2px solid #1A1714;border-radius:18px;
                 padding:28px 16px 16px;text-align:center;box-shadow:3px 3px 0 #1A1714;">
              <div style="font-size:36px;margin-bottom:10px">{icon}</div>
              <div style="font-size:16px;font-weight:800;margin-bottom:4px;color:#1A1714">{title}</div>
              <div style="font-size:12px;color:#9A9088;font-weight:500;margin-bottom:14px">{subtitle}</div>
            </div>
            """, unsafe_allow_html=True)
            # Clickable button right below card
            if st.button(f"Open {title} →", key=f"home_nav_{title}", use_container_width=True):
                st.switch_page(page)


# ──────────────────────────────────────────────
# MAIN ROUTER
# ──────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        show_login()
        st.stop()

    user = st.session_state["user"]

    if not user.get("job_title"):
        show_profile_setup()
        st.stop()

    show_sidebar()
    show_home()


if __name__ == "__main__":
    main()
