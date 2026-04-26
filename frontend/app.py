# app.py
# Streamlit frontend for the Skill Assessment Agent.
# Three-phase UI: Upload → Conversational Assessment → Report & Learning Plan.
# Communicates with the FastAPI backend at BACKEND_URL.

import streamlit as st
import requests
import json
import os
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="SkillSense AI — Skill Assessment Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Chat messages */
.chat-message {
    padding: 1rem 1.2rem;
    border-radius: 12px;
    margin: 0.5rem 0;
    max-width: 85%;
    line-height: 1.6;
    font-size: 0.95rem;
}
.chat-user {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    margin-left: auto;
    border-bottom-right-radius: 2px;
}
.chat-assistant {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom-left-radius: 2px;
}

/* Score card */
.score-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
}
.score-number {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}
.score-high { color: #10b981; }
.score-mid  { color: #f59e0b; }
.score-low  { color: #ef4444; }

/* Phase card */
.phase-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.08));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin: 0.8rem 0;
}

/* Quick win */
.quick-win {
    background: rgba(16,185,129,0.1);
    border-left: 3px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
}

/* Match score banner */
.match-banner {
    background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.3));
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1rem;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ────────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "upload",           # "upload" | "chat" | "report"
        "session_id": None,
        "candidate_name": None,
        "target_role": None,
        "match_score": None,
        "skills_to_assess": [],
        "chat_messages": [],         # list of {"role": str, "content": str}
        "current_skill": None,
        "skill_index": 0,
        "total_skills": 0,
        "assessment_complete": False,
        "report_data": None,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─── Helper: API Calls ───────────────────────────────────────────────────────

def api_upload(resume_bytes: bytes, resume_filename: str, jd_text: str) -> dict:
    """Upload resume + JD, start session."""
    resp = requests.post(
        f"{BACKEND_URL}/upload",
        files={"resume": (resume_filename, resume_bytes, "application/pdf")},
        data={"jd_text": jd_text},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def api_chat(session_id: str, message: str) -> dict:
    """Send a chat message."""
    resp = requests.post(
        f"{BACKEND_URL}/chat",
        json={"session_id": session_id, "message": message},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def api_report(session_id: str) -> dict:
    """Fetch the final report."""
    resp = requests.get(f"{BACKEND_URL}/report/{session_id}", timeout=180)
    resp.raise_for_status()
    return resp.json()


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧠 SkillSense AI")
    st.markdown("*Skill Assessment & Learning Plan Agent*")
    st.divider()

    if st.session_state.phase == "upload":
        st.markdown("### 📋 Step 1: Upload Documents")
        st.markdown("Upload your resume and paste the job description to get started.")

    elif st.session_state.phase in ("chat", "report"):
        if st.session_state.candidate_name:
            st.markdown(f"**👤 Candidate:** {st.session_state.candidate_name}")
        if st.session_state.target_role:
            st.markdown(f"**🎯 Target Role:** {st.session_state.target_role}")
        if st.session_state.match_score is not None:
            score = st.session_state.match_score
            color = "#10b981" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
            st.markdown(f"**📊 Profile Match:** <span style='color:{color};font-weight:700'>{score}%</span>", unsafe_allow_html=True)
        st.divider()

        if st.session_state.skills_to_assess:
            st.markdown("**🔍 Skills Being Assessed:**")
            for i, skill in enumerate(st.session_state.skills_to_assess):
                idx = st.session_state.skill_index
                if st.session_state.phase == "report":
                    st.markdown(f"✅ {skill}")
                elif i < idx:
                    st.markdown(f"✅ ~~{skill}~~")
                elif i == idx:
                    st.markdown(f"🔵 **{skill}** ← *current*")
                else:
                    st.markdown(f"⬜ {skill}")

    st.divider()

    if st.session_state.phase != "upload":
        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    st.markdown("<small style='color:#666'>Powered by Claude claude-sonnet-4-20250514 · Built for Catalyst Hackathon</small>", unsafe_allow_html=True)


# ─── PHASE 1: UPLOAD ─────────────────────────────────────────────────────────

if st.session_state.phase == "upload":
    st.markdown("# 🧠 SkillSense AI")
    st.markdown("### AI-Powered Skill Assessment & Personalized Learning Plan")
    st.markdown("Upload your resume and the job description. I'll assess your skills through a short conversation and build you a hyper-personalized learning plan.")

    st.divider()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### 📄 Resume")
        resume_file = st.file_uploader(
            "Upload your resume (PDF or TXT)",
            type=["pdf", "txt"],
            help="Your resume will be parsed to extract skills and experience.",
            key="resume_uploader",
        )
        if resume_file:
            st.success(f"✅ {resume_file.name} uploaded ({resume_file.size // 1024} KB)")

    with col2:
        st.markdown("#### 💼 Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder="Paste the full job description text here...\n\nTip: Include the full JD with requirements, responsibilities, and nice-to-haves for the best results.",
            key="jd_textarea",
        )
        if jd_text:
            st.caption(f"📝 {len(jd_text.split())} words")

    st.divider()

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        start_btn = st.button(
            "🚀 Start Assessment",
            use_container_width=True,
            type="primary",
            disabled=(resume_file is None or not jd_text.strip()),
        )

    if start_btn:
        with st.spinner("📡 Analyzing your resume and the job description... (this takes ~30 seconds)"):
            try:
                result = api_upload(
                    resume_bytes=resume_file.read(),
                    resume_filename=resume_file.name,
                    jd_text=jd_text,
                )
                st.session_state.session_id = result["session_id"]
                st.session_state.candidate_name = result["candidate_name"]
                st.session_state.target_role = result["target_role"]
                st.session_state.match_score = result["match_score"]
                st.session_state.skills_to_assess = result["skills_to_assess"]
                st.session_state.total_skills = len(result["skills_to_assess"])
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": result["welcome_message"]}
                ]
                st.session_state.phase = "chat"
                st.session_state.error = None
                st.rerun()
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the backend. Make sure `uvicorn backend.main:app --reload` is running.")
            except requests.exceptions.HTTPError as e:
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"❌ Upload failed: {detail}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

    # Sample data hint
    with st.expander("💡 Don't have a resume? Use sample data"):
        st.markdown("You can find sample inputs in the `samples/` directory:")
        st.code("samples/sample_jd.txt\nsamples/sample_resume.txt", language="bash")


# ─── PHASE 2: CHAT ───────────────────────────────────────────────────────────

elif st.session_state.phase == "chat":
    st.markdown(f"## 💬 Assessment Chat")

    # Progress bar
    if st.session_state.total_skills > 0:
        progress = st.session_state.skill_index / st.session_state.total_skills
        current_skill_name = (
            st.session_state.skills_to_assess[st.session_state.skill_index]
            if st.session_state.skill_index < st.session_state.total_skills
            else "Done"
        )
        st.progress(progress, text=f"Skill {st.session_state.skill_index + 1} of {st.session_state.total_skills}: **{current_skill_name}**")

    st.divider()

    # Chat display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧠"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])

    # Input (disabled when assessment is complete)
    if st.session_state.assessment_complete:
        st.info("✅ Assessment complete! Fetching your personalized learning plan...")
        with st.spinner("Generating your learning plan... (~20 seconds)"):
            try:
                report = api_report(st.session_state.session_id)
                st.session_state.report_data = report
                st.session_state.phase = "report"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to generate report: {str(e)}")
    else:
        user_input = st.chat_input("Type your response here...")
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            with st.spinner("Thinking..."):
                try:
                    result = api_chat(st.session_state.session_id, user_input)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": result["reply"]}
                    )
                    st.session_state.skill_index = result["skill_index"]
                    st.session_state.current_skill = result["current_skill"]

                    if result["is_complete"] or result["stage"] in ("scoring", "report"):
                        st.session_state.assessment_complete = True

                except requests.exceptions.HTTPError as e:
                    try:
                        detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"❌ Chat error: {detail}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

            st.rerun()


# ─── PHASE 3: REPORT ─────────────────────────────────────────────────────────

elif st.session_state.phase == "report":
    report = st.session_state.report_data

    if not report:
        st.error("No report data found. Please restart the assessment.")
        st.stop()

    plan = report.get("learning_plan", {})
    scores = report.get("scores", [])
    gap = report.get("gap_analysis", {})

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"# 📊 Assessment Report")
    st.markdown(f"**{report.get('candidate_name', 'Candidate')}** · Target: **{report.get('target_role', 'Role')}**")
    st.divider()

    # ── Overall Match + Readiness ─────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        match_score = report.get("overall_match_score", 0)
        st.metric("Profile Match", f"{match_score}%")
    with col2:
        readiness = plan.get("readiness_level", "—")
        st.metric("Readiness", readiness)
    with col3:
        total_phases = len(plan.get("learning_phases", []))
        st.metric("Learning Phases", str(total_phases))

    st.divider()

    # ── Overall Recommendation ───────────────────────────────────────────
    if plan.get("overall_recommendation"):
        st.info(f"💡 {plan['overall_recommendation']}")

    # ── Skill Scores ─────────────────────────────────────────────────────
    st.markdown("## 🎯 Skill Assessment Results")
    if scores:
        cols = st.columns(min(len(scores), 3))
        for i, score in enumerate(scores):
            col = cols[i % 3]
            with col:
                s = score.get("proficiency_score", 0)
                color_cls = "score-high" if s >= 7 else "score-mid" if s >= 4 else "score-low"
                color_hex = "#10b981" if s >= 7 else "#f59e0b" if s >= 4 else "#ef4444"
                st.markdown(f"""
                <div class='score-card'>
                    <div style='font-weight:600;margin-bottom:0.3rem'>{score.get('skill_name','')}</div>
                    <div class='score-number' style='color:{color_hex}'>{s}<span style='font-size:1rem;font-weight:400;color:#888'>/10</span></div>
                    <div style='font-size:0.8rem;color:#aaa;margin-top:0.2rem'>{score.get('proficiency_label','').capitalize()} · {score.get('confidence','').capitalize()} confidence</div>
                    <div style='font-size:0.82rem;margin-top:0.6rem;color:#ccc'>{score.get('score_reasoning','')}</div>
                    <div style='font-size:0.8rem;margin-top:0.5rem'>
                        {'⏱ ' + str(score.get('estimated_gap_weeks', 0)) + ' weeks to close gap' if score.get('estimated_gap_weeks', 0) > 0 else '✅ Ready for role'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No skill scores available.")

    st.divider()

    # ── Learning Plan ─────────────────────────────────────────────────────
    st.markdown("## 📚 Personalized Learning Plan")

    phases = plan.get("learning_phases", [])
    for phase in phases:
        with st.expander(
            f"**Phase {phase.get('phase_number')}: {phase.get('phase_name')}** — {phase.get('duration_weeks')} weeks",
            expanded=(phase.get("phase_number") == 1),
        ):
            st.markdown(f"*{phase.get('focus', '')}*")
            for skill in phase.get("skills", []):
                st.markdown(f"#### 🔧 {skill.get('skill_name')}")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Current Level:** {skill.get('current_level')}")
                    st.markdown(f"**Target Level:** {skill.get('target_level')}")
                with c2:
                    st.markdown(f"**Weekly Commitment:** {skill.get('weekly_commitment_hours')}h/week")
                    st.markdown(f"**Why Now:** {skill.get('why_prioritized')}")

                st.markdown(f"🏆 **Milestone:** {skill.get('milestone')}")

                if skill.get("resources"):
                    st.markdown("**📖 Resources:**")
                    for res in skill.get("resources", []):
                        url = res.get("url")
                        title = res.get("title", "Resource")
                        link = f"[{title}]({url})" if url else title
                        st.markdown(
                            f"- {link} · *{res.get('provider')}* · ~{res.get('estimated_hours')}h"
                            f"\n  > {res.get('why_this_resource')}"
                        )
                st.markdown("---")

    # ── Quick Wins ────────────────────────────────────────────────────────
    quick_wins = plan.get("quick_wins", [])
    if quick_wins:
        st.markdown("## ⚡ Quick Wins — Do These in 48 Hours")
        for qw in quick_wins:
            st.markdown(f"""
            <div class='quick-win'>
                <strong>→ {qw.get('action')}</strong><br>
                <small style='color:#6ee7b7'>{qw.get('impact')}</small>
            </div>
            """, unsafe_allow_html=True)

    # ── Skills to Skip ────────────────────────────────────────────────────
    skip_items = plan.get("skills_to_skip_for_now", [])
    if skip_items:
        with st.expander("⏭ Skills to Defer for Now"):
            for item in skip_items:
                st.markdown(f"- **{item.get('skill_name')}**: {item.get('reason')}")

    # ── Motivational Note ─────────────────────────────────────────────────
    if plan.get("motivational_note"):
        st.markdown("---")
        st.success(f"💬 {plan['motivational_note']}")

    st.divider()

    # ── Download ──────────────────────────────────────────────────────────
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="⬇️ Download Full Report (JSON)",
            data=json.dumps(report, indent=2),
            file_name=f"skillsense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_dl2:
        plan_md = _generate_plan_markdown(plan, scores, report)
        st.download_button(
            label="⬇️ Download Learning Plan (Markdown)",
            data=plan_md,
            file_name=f"learning_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


def _generate_plan_markdown(plan: dict, scores: list, report: dict) -> str:
    """Generate a clean markdown export of the learning plan."""
    lines = [
        f"# Learning Plan: {plan.get('candidate_name')}",
        f"**Target Role:** {plan.get('target_role')}",
        f"**Readiness:** {plan.get('readiness_level')}",
        f"**Profile Match:** {report.get('overall_match_score')}%",
        "",
        "## Overall Assessment",
        plan.get("overall_recommendation", ""),
        "",
        "## Skill Scores",
    ]
    for s in scores:
        lines.append(f"- **{s.get('skill_name')}**: {s.get('proficiency_score')}/10 ({s.get('proficiency_label')})")
        lines.append(f"  - {s.get('score_reasoning')}")

    lines.extend(["", "## Learning Plan"])
    for phase in plan.get("learning_phases", []):
        lines.append(f"\n### Phase {phase.get('phase_number')}: {phase.get('phase_name')} ({phase.get('duration_weeks')} weeks)")
        lines.append(f"*{phase.get('focus')}*")
        for skill in phase.get("skills", []):
            lines.append(f"\n#### {skill.get('skill_name')}")
            lines.append(f"- Current: {skill.get('current_level')} → Target: {skill.get('target_level')}")
            lines.append(f"- Milestone: {skill.get('milestone')}")
            for res in skill.get("resources", []):
                url = res.get("url", "")
                lines.append(f"- [{res.get('title')}]({url}) ({res.get('provider')}, ~{res.get('estimated_hours')}h)")

    lines.extend(["", "## Quick Wins"])
    for qw in plan.get("quick_wins", []):
        lines.append(f"- **{qw.get('action')}** — {qw.get('impact')}")

    if plan.get("motivational_note"):
        lines.extend(["", "---", f"*{plan.get('motivational_note')}*"])

    return "\n".join(lines)
