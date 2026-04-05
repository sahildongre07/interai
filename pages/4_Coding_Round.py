"""
pages/4_Coding_Round.py — AI coding interview simulator.
Problem panel + code editor + AI code review.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.llm_utils import generate_coding_question, get_code_feedback
from utils.storage_utils import save_session, get_user_sessions

# ─── Auth guard ────────────────────────────────────────────────────────────────
if "user" not in st.session_state or not st.session_state["user"].get("job_title"):
    st.warning("Please log in and complete your profile first.")
    st.stop()

user = st.session_state["user"]

# ─── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Instrument Serif',serif;font-size:36px;line-height:1.1;margin-bottom:4px">
  Coding <em style="color:#FF5C3A">round</em> 💻
</div>
""", unsafe_allow_html=True)
companies_str = " · ".join(user.get("target_companies", [])[:3]) or "top companies"
st.markdown(f"AI-curated problems for **{user.get('job_title','your role')}** at {companies_str}")
st.markdown("---")

# ─── State ─────────────────────────────────────────────────────────────────────
if "coding_problem" not in st.session_state:
    st.session_state.coding_problem = None
if "coding_asked" not in st.session_state:
    st.session_state.coding_asked = []
if "code_feedback" not in st.session_state:
    st.session_state.code_feedback = None
if "code_saved" not in st.session_state:
    st.session_state.code_saved = False
if "user_code" not in st.session_state:
    st.session_state.user_code = ""
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "python"

# ─── Stats bar ─────────────────────────────────────────────────────────────────
all_sessions = get_user_sessions(user["id"])
coding_sessions = [s for s in all_sessions if s.get("type") == "coding"]
avg_score = round(sum(s.get("overall_score", 0) for s in coding_sessions) / len(coding_sessions)) if coding_sessions else 0
best_score = max((s.get("overall_score", 0) for s in coding_sessions), default=0)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("✅ Solved", f"{len(coding_sessions)}")
with col2:
    st.metric("📈 Avg Score", f"{avg_score}/100")
with col3:
    st.metric("🏆 Best Score", f"{best_score}/100")
with col4:
    st.metric("💻 Language", st.session_state.selected_lang.title())

st.markdown("---")

# ─── Generate new problem ──────────────────────────────────────────────────────
col_gen, col_lang = st.columns([2, 1])
with col_gen:
    if st.button("⚡ Generate New Problem", type="primary", use_container_width=True):
        with st.spinner("🤖 Generating a coding problem tailored to your profile..."):
            try:
                problem = generate_coding_question(
                    job_title=user.get("job_title", "Software Engineer"),
                    companies=user.get("target_companies", []),
                    experience=user.get("experience_level", "Fresher"),
                    asked_titles=st.session_state.coding_asked[-8:],
                )
                st.session_state.coding_problem = problem
                title = problem.get("title", "Problem")
                if title not in st.session_state.coding_asked:
                    st.session_state.coding_asked.append(title)
                # Load starter code
                starter = problem.get("starter_code", {})
                st.session_state.user_code = starter.get(st.session_state.selected_lang, starter.get("python", "# Write your solution here\n"))
                st.session_state.code_feedback = None
                st.session_state.code_saved = False
                st.rerun()
            except Exception as e:
                st.error(f"Could not generate problem: {e}")
                st.info("Check your OPENROUTER_API_KEY in .streamlit/secrets.toml")

with col_lang:
    lang = st.selectbox(
        "Language",
        ["python", "javascript", "java", "cpp"],
        format_func=lambda x: {"python": "Python 3", "javascript": "JavaScript", "java": "Java", "cpp": "C++"}[x],
        index=["python", "javascript", "java", "cpp"].index(st.session_state.selected_lang),
    )
    if lang != st.session_state.selected_lang:
        st.session_state.selected_lang = lang
        if st.session_state.coding_problem:
            starter = st.session_state.coding_problem.get("starter_code", {})
            st.session_state.user_code = starter.get(lang, starter.get("python", ""))
        st.rerun()

# ─── Problem + Editor ──────────────────────────────────────────────────────────
if st.session_state.coding_problem is None:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#FEFCF7;border:2px dashed #DDD8CE;
         border-radius:20px;margin-top:20px">
      <div style="font-size:48px;margin-bottom:12px">💻</div>
      <div style="font-family:'Instrument Serif',serif;font-size:22px;margin-bottom:8px">No problem loaded</div>
      <div style="color:#9A9088;font-size:14px">Click "Generate New Problem" to get started</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

problem = st.session_state.coding_problem

col_prob, col_editor = st.columns([1, 1])

# ─── Problem Panel ─────────────────────────────────────────────────────────────
with col_prob:
    DIFF_COLORS = {"Easy": "#10B981", "Medium": "#F59E0B", "Hard": "#FF5C3A"}
    diff = problem.get("difficulty", "Medium")
    diff_color = DIFF_COLORS.get(diff, "#666")

    st.markdown(f"""
    <div style="background:#FEFCF7;border:2px solid #1A1714;border-radius:20px;
         box-shadow:3px 3px 0 #1A1714;overflow:hidden">
      <div style="padding:14px 18px;border-bottom:2px solid #EDE9DF;background:#F5F2EB;
           display:flex;align-items:center;justify-content:space-between">
        <div style="font-family:'Instrument Serif',serif;font-size:17px">
          📄 {problem.get('title', 'Problem')}
        </div>
        <div style="display:flex;gap:6px">
          <span style="background:{'#EDFDF5' if diff=='Easy' else '#FFFBEB' if diff=='Medium' else '#FFF0EC'};
               border:1.5px solid #1A1714;border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;color:{diff_color}">
            {'✅' if diff=='Easy' else '⚡' if diff=='Medium' else '🔥'} {diff}
          </span>
          <span style="background:#EEF4FF;border:1.5px solid #1A1714;border-radius:6px;
               padding:3px 8px;font-size:11px;font-weight:700;color:#3B82F6">
            🏢 {problem.get('company', '')}
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tags
    tags = problem.get("topic", "").split("/")
    tag_html = " ".join([f'<span style="background:#F4F0FF;border:1.5px solid #1A1714;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700;color:#8B5CF6">{t.strip()}</span>' for t in tags if t.strip()])
    st.markdown(tag_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Description
    st.markdown(f"<div style='font-size:13.5px;line-height:1.75;color:#4A4540'>{problem.get('description','')}</div>", unsafe_allow_html=True)

    # Examples
    st.markdown("**Examples:**")
    for ex in problem.get("examples", []):
        explanation = f"\n<b>Explanation:</b> {ex.get('explanation','')}" if ex.get('explanation') else ""
        st.markdown(f"""
        <div style="background:#EDE9DF;border:1.5px solid #DDD8CE;border-radius:10px;
             padding:12px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;
             line-height:1.6;color:#4A4540;margin-bottom:8px;white-space:pre-wrap">
<b>Input:</b>  {ex.get('input','')}
<b>Output:</b> {ex.get('output','')}{explanation}</div>
        """, unsafe_allow_html=True)

    # Constraints
    st.markdown("**Constraints:**")
    for c in problem.get("constraints", []):
        st.markdown(f"• {c}")

    # Hint
    if problem.get("hint"):
        with st.expander("💡 Show Hint"):
            st.info(problem["hint"])

# ─── Code Editor ───────────────────────────────────────────────────────────────
with col_editor:
    st.markdown("""
    <div style="background:#0F1117;border:2px solid #1A1714;border-radius:20px;
         overflow:hidden;box-shadow:3px 3px 0 #1A1714">
      <div style="padding:10px 14px;border-bottom:1.5px solid #2A2D3A;background:#171923;
           display:flex;align-items:center;gap:8px">
        <div style="width:11px;height:11px;border-radius:50%;background:#FF5F57"></div>
        <div style="width:11px;height:11px;border-radius:50%;background:#FFBD2E"></div>
        <div style="width:11px;height:11px;border-radius:50%;background:#28C840"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#6B7280;margin-left:8px">
          solution.{{"python":"py","javascript":"js","java":"java","cpp":"cpp"}[st.session_state.selected_lang]}
        </span>
      </div>
    </div>
    """.replace('st.session_state.selected_lang', f'"{st.session_state.selected_lang}"'), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#0F1117;border-left:2px solid #1A1714;border-right:2px solid #1A1714;
         padding:4px 0">
      <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#6B7280;padding-left:12px">
        ⏱ Timer starts when you begin typing
      </span>
    </div>
    """, unsafe_allow_html=True)

    user_code = st.text_area(
        "Code editor",
        value=st.session_state.user_code,
        height=380,
        key="code_textarea",
        label_visibility="collapsed",
        help="Write your solution here. Tab key inserts spaces.",
        placeholder="Write your solution here...",
    )
    st.session_state.user_code = user_code

    char_count = len(user_code)
    line_count = user_code.count("\n") + 1
    st.caption(f"📝 {line_count} lines · {char_count} chars")

    col_run, col_submit, col_reset = st.columns(3)
    with col_run:
        run_btn = st.button("▶ Run Tests", use_container_width=True)
    with col_submit:
        submit_btn = st.button("🚀 Submit & Get AI Review", use_container_width=True, type="primary")
    with col_reset:
        if st.button("↺ Reset", use_container_width=True):
            starter = problem.get("starter_code", {})
            st.session_state.user_code = starter.get(st.session_state.selected_lang, starter.get("python", ""))
            st.session_state.code_feedback = None
            st.session_state.code_saved = False
            st.rerun()

    # Run tests (simulated)
    if run_btn:
        test_cases = problem.get("examples", [])
        has_logic = len(user_code.strip()) > 80 and "pass" not in user_code and "Your solution" not in user_code

        with st.expander("🧪 Test Results", expanded=True):
            if has_logic:
                st.success(f"✅ {len(test_cases)}/{len(test_cases)} test cases passed (simulated)")
                for i, tc in enumerate(test_cases):
                    st.markdown(f"✅ **Test {i+1}:** Input: `{tc.get('input','')}` → Expected: `{tc.get('output','')}`")
            else:
                st.error(f"❌ 0/{len(test_cases)} test cases passed — complete your solution first!")
                for i, tc in enumerate(test_cases):
                    st.markdown(f"❌ **Test {i+1}:** Input: `{tc.get('input','')}` → Expected: `{tc.get('output','')}` — returned `None`")

# ─── AI Code Review ────────────────────────────────────────────────────────────
if submit_btn:
    if len(user_code.strip()) < 20:
        st.error("Please write some code before submitting!")
    else:
        with st.spinner("🧠 Analysing your code with AI..."):
            try:
                feedback = get_code_feedback(problem, user_code, st.session_state.selected_lang)
                st.session_state.code_feedback = feedback
                st.session_state.code_saved = False
                st.rerun()
            except Exception as e:
                st.error(f"AI code review failed: {e}")
                st.info("Check your OPENROUTER_API_KEY in .streamlit/secrets.toml")

if st.session_state.code_feedback:
    fb = st.session_state.code_feedback
    score = fb.get("score", 0)
    verdict = fb.get("verdict", "Average")

    st.markdown("---")

    # Hero result
    VERDICT_COLORS = {
        "Optimal": "#10B981",
        "Good": "#B14EFF",
        "Average": "#F59E0B",
        "Needs Work": "#FF5C3A",
    }
    v_color = VERDICT_COLORS.get(verdict, "#B14EFF")
    score_pct = score / 100

    st.markdown(f"""
    <div style="background:#0F1117;border:2px solid #1A1714;border-radius:20px;
         padding:28px 32px;box-shadow:4px 4px 0 #1A1714;margin-bottom:18px;
         display:flex;align-items:center;gap:24px">
      <div style="text-align:center;min-width:90px">
        <div style="font-family:'Instrument Serif',serif;font-size:52px;line-height:1;color:{v_color}">{score}</div>
        <div style="font-size:12px;color:#6B7280;font-weight:600">/ 100</div>
      </div>
      <div>
        <div style="font-family:'Instrument Serif',serif;font-size:22px;color:white;margin-bottom:8px">
          {fb.get('optimal_approach', 'Code reviewed!')[:80]}
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <span style="background:rgba(16,185,129,.1);border:1.5px solid rgba(16,185,129,.4);
               border-radius:6px;padding:3px 10px;font-size:11.5px;font-weight:700;color:#34D399">
            {verdict}
          </span>
          <span style="background:rgba(59,130,246,.1);border:1.5px solid rgba(59,130,246,.4);
               border-radius:6px;padding:3px 10px;font-size:11.5px;font-weight:700;color:#93C5FD">
            ⏱ {fb.get('user_time_complexity','?')} time
          </span>
          <span style="background:rgba(245,158,11,.1);border:1.5px solid rgba(245,158,11,.4);
               border-radius:6px;padding:3px 10px;font-size:11.5px;font-weight:700;color:#FCD34D">
            💾 {fb.get('user_space_complexity','?')} space
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <span style="font-family:'Instrument Serif',serif;font-size:22px">Code Review</span>
      <span style="font-size:11.5px;color:#9A9088;background:#EDE9DF;border:1.5px solid #DDD8CE;
           padding:2px 10px;border-radius:20px;font-weight:600">Llama 3.3 70B · free</span>
    </div>
    """, unsafe_allow_html=True)

    # Feedback grid
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""<div style="background:#EDFDF5;border:2px solid #1A1714;border-radius:14px;
             padding:18px;box-shadow:2px 2px 0 #1A1714;height:100%">""", unsafe_allow_html=True)
        st.markdown("**✅ What's correct**")
        for pt in fb.get("what_is_correct", []):
            st.markdown(f"→ {pt}")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("""<div style="background:#FFFBEB;border:2px solid #1A1714;border-radius:14px;
             padding:18px;box-shadow:2px 2px 0 #1A1714;height:100%">""", unsafe_allow_html=True)
        st.markdown("**⚡ Improvements needed**")
        for pt in fb.get("improvements", []):
            st.markdown(f"→ {pt}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Complexity table
    st.markdown("**📊 Complexity Analysis**")
    comp_data = {
        "": ["Time Complexity", "Space Complexity"],
        "Your Solution": [fb.get("user_time_complexity", "?"), fb.get("user_space_complexity", "?")],
        "Optimal": [fb.get("optimal_time_complexity", "?"), fb.get("optimal_space_complexity", "?")],
    }
    st.table(comp_data)

    # Optimal approach
    st.markdown("""<div style="background:#EEF4FF;border:2px solid #1A1714;border-radius:14px;
         padding:18px;box-shadow:2px 2px 0 #1A1714;margin-bottom:14px">""", unsafe_allow_html=True)
    st.markdown("**💡 Optimal Approach**")
    st.markdown(fb.get("optimal_approach", ""))
    st.markdown("</div>", unsafe_allow_html=True)

    # Optimal solution code
    if fb.get("optimal_solution"):
        with st.expander("📋 View Optimal Solution"):
            st.code(fb["optimal_solution"], language=st.session_state.selected_lang)

    # Save session
    if not st.session_state.code_saved:
        session_data = {
            "type": "coding",
            "problem_title": problem.get("title", ""),
            "question": problem.get("title", ""),
            "difficulty": problem.get("difficulty", ""),
            "company": problem.get("company", ""),
            "language": st.session_state.selected_lang,
            "user_code": user_code,
            "overall_score": score,
            "verdict": verdict,
            "user_time_complexity": fb.get("user_time_complexity"),
            "user_space_complexity": fb.get("user_space_complexity"),
            "optimal_time_complexity": fb.get("optimal_time_complexity"),
            "optimal_space_complexity": fb.get("optimal_space_complexity"),
            "ai_feedback": {
                "what_went_well": fb.get("what_is_correct", []),
                "areas_to_improve": fb.get("improvements", []),
                "ideal_answer_structure": [],
                "example_strong_answer": fb.get("optimal_approach", ""),
            },
        }
        try:
            save_session(user["id"], session_data)
            st.session_state.code_saved = True
        except Exception:
            pass

    if st.session_state.code_saved:
        st.markdown(f"""
        <div class="save-success">✅ Coding session saved! Score: {score}/100</div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ Next Problem", use_container_width=True, type="primary"):
            with st.spinner("Generating next problem..."):
                try:
                    new_problem = generate_coding_question(
                        job_title=user.get("job_title", "Software Engineer"),
                        companies=user.get("target_companies", []),
                        experience=user.get("experience_level", "Fresher"),
                        asked_titles=st.session_state.coding_asked,
                    )
                    st.session_state.coding_problem = new_problem
                    title = new_problem.get("title", "")
                    if title not in st.session_state.coding_asked:
                        st.session_state.coding_asked.append(title)
                    starter = new_problem.get("starter_code", {})
                    st.session_state.user_code = starter.get(st.session_state.selected_lang, starter.get("python", ""))
                    st.session_state.code_feedback = None
                    st.session_state.code_saved = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    with col2:
        if st.button("📊 View Dashboard →", use_container_width=True):
            st.switch_page("pages/3_Dashboard.py")
