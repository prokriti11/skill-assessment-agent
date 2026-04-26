# main.py
# FastAPI application — the orchestration layer for the Skill Assessment Agent.
# Wires all 6 agents together via a state machine. Uses Groq (free tier).
#
# Endpoints:
#   POST /upload   — accept resume PDF + JD text, run parse + gap analysis, open session
#   POST /chat     — handle conversation turn, route to assessor or orchestrator
#   GET  /report   — trigger scoring + plan generation, return full report
#   GET  /session/{session_id} — get current session status
#   GET  /health   — health check

import os
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.models.schemas import (
    SessionState, SessionStage, ConversationMessage,
    SkillAssessmentState,
    ChatRequest, ChatResponse, UploadResponse, ReportResponse,
)
from backend.utils.session_store import create_session, get_session, save_session
from backend.utils.pdf_extractor import extract_text_from_pdf, extract_text_from_string
from backend.agents.jd_parser import parse_jd
from backend.agents.resume_parser import parse_resume
from backend.agents.gap_analyzer import analyze_gaps
from backend.agents.skill_assessor import get_next_assessor_message, get_resume_evidence_for_skill
from backend.agents.proficiency_scorer import score_skill
from backend.agents.learning_plan import generate_learning_plan
from backend.prompts.all_prompts import ORCHESTRATOR_PROMPT

from backend.utils.llm_client import call_llm
MODEL = "llama-3.3-70b-versatile"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Skill Assessment Agent API is starting up...")
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set. All LLM calls will fail.")
    yield
    print("👋 Skill Assessment Agent API shutting down.")


app = FastAPI(
    title="Skill Assessment Agent API",
    description="AI-powered skill assessment and personalized learning plan generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "api_key_set": bool(os.environ.get("GROQ_API_KEY")),
        "model": MODEL,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload — Parse resume + JD, run gap analysis, create session
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/upload", response_model=UploadResponse)
async def upload(
    resume: UploadFile = File(..., description="Resume PDF file"),
    jd_text: str = Form(..., description="Job description text"),
):
    """
    Step 1: Upload resume PDF + JD text.
    Runs: PDF extraction → resume parse → JD parse → gap analysis → session creation.
    Returns a session_id and the welcome message.
    """
    # ── 1. Extract resume text ──────────────────────────────────────────────
    try:
        resume_bytes = await resume.read()
        if resume.content_type == "application/pdf" or resume.filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(resume_bytes)
        else:
            # Treat as plain text
            resume_text = extract_text_from_string(resume_bytes.decode("utf-8", errors="ignore"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read resume: {str(e)}")

    if not jd_text or len(jd_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description is too short. Please provide a full JD.")

    # ── 2. Parse JD + Resume in parallel ───────────────────────────────────
    try:
        jd_profile, resume_profile = await asyncio.gather(
            asyncio.to_thread(parse_jd, jd_text),
            asyncio.to_thread(parse_resume, resume_text),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── 3. Run gap analysis ─────────────────────────────────────────────────
    try:
        gap_analysis = await asyncio.to_thread(analyze_gaps, jd_profile, resume_profile)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── 4. Create session ────────────────────────────────────────────────────
    session_id = create_session()
    state = get_session(session_id)

    state.jd_text = jd_text
    state.jd_profile = jd_profile
    state.resume_text = resume_text
    state.resume_profile = resume_profile
    state.gap_analysis = gap_analysis
    state.skills_to_assess = gap_analysis.skills_to_assess
    state.stage = SessionStage.WELCOME

    # Initialize skill states
    for skill in state.skills_to_assess:
        state.skill_states[skill] = SkillAssessmentState(skill_name=skill)

    # ── 5. Generate welcome message ──────────────────────────────────────────
    welcome_msg = _generate_orchestrator_message(state)
    state.chat_history.append(ConversationMessage(role="assistant", content=welcome_msg))
    state.stage = SessionStage.CONFIRM_SKILLS

    save_session(state)

    return UploadResponse(
        session_id=session_id,
        candidate_name=resume_profile.candidate_name,
        target_role=jd_profile.job_title,
        match_score=gap_analysis.overall_match_score,
        skills_to_assess=state.skills_to_assess,
        welcome_message=welcome_msg,
        stage=state.stage.value,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /chat — Handle a conversation turn
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Step 2: Send a candidate message and get the next assistant reply.
    Routes through the state machine: orchestrator → assessor → transition → wrap-up.
    """
    state = get_session(request.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Add user message to global chat history
    state.chat_history.append(ConversationMessage(role="user", content=user_message))

    reply, state = await _route_message(state, user_message)

    state.chat_history.append(ConversationMessage(role="assistant", content=reply))
    save_session(state)

    current_skill = (
        state.skills_to_assess[state.current_skill_index]
        if state.current_skill_index < len(state.skills_to_assess)
        else None
    )

    return ChatResponse(
        session_id=state.session_id,
        reply=reply,
        stage=state.stage.value,
        current_skill=current_skill,
        skill_index=state.current_skill_index,
        total_skills=len(state.skills_to_assess),
        is_complete=state.stage == SessionStage.REPORT,
    )


async def _route_message(state: SessionState, user_message: str) -> tuple[str, SessionState]:
    """Route a user message to the correct handler based on current stage."""

    # ── CONFIRM_SKILLS: user says "yes/ready" → start first assessment ────
    if state.stage == SessionStage.CONFIRM_SKILLS:
        state.stage = SessionStage.ASSESSING
        reply = await _start_skill_assessment(state)
        return reply, state

    # ── ASSESSING: user is answering an assessor question ─────────────────
    if state.stage == SessionStage.ASSESSING:
        return await _handle_assessment_turn(state, user_message)

    # ── TRANSITION: user acknowledges, continue to next skill ─────────────
    if state.stage == SessionStage.TRANSITION:
        state.current_skill_index += 1
        if state.current_skill_index >= len(state.skills_to_assess):
            state.stage = SessionStage.WRAP_UP
            reply = _generate_orchestrator_message(state)
            state.stage = SessionStage.SCORING
            return reply, state
        else:
            state.stage = SessionStage.ASSESSING
            reply = await _start_skill_assessment(state)
            return reply, state

    # ── WRAP_UP / SCORING: user message received, start scoring ───────────
    if state.stage in (SessionStage.WRAP_UP, SessionStage.SCORING):
        reply = "I'm processing your results right now — your personalized learning plan will be ready in just a moment! 🎯"
        state.stage = SessionStage.REPORT
        return reply, state

    # ── REPORT: already done ───────────────────────────────────────────────
    if state.stage == SessionStage.REPORT:
        return "Your assessment is complete! Check your personalized learning plan above. 📚", state

    # Fallback
    return "I'm ready when you are! Let's continue.", state


async def _start_skill_assessment(state: SessionState) -> str:
    """Open the assessment conversation for the current skill."""
    skill_name = state.skills_to_assess[state.current_skill_index]
    skill_state = state.skill_states[skill_name]

    # Find resume evidence
    candidate_claim, resume_evidence = get_resume_evidence_for_skill(
        skill_name, state.resume_profile.skills_claimed
    )

    # Find expected level from JD
    expected_level = "intermediate"
    for jd_skill in state.jd_profile.required_skills:
        if jd_skill.skill_name.lower() == skill_name.lower():
            expected_level = jd_skill.expected_proficiency.value
            break

    reply, updated_skill_state = await asyncio.to_thread(
        get_next_assessor_message,
        skill_state, candidate_claim, resume_evidence, expected_level, None
    )

    state.skill_states[skill_name] = updated_skill_state
    return reply


async def _handle_assessment_turn(state: SessionState, user_message: str) -> tuple[str, SessionState]:
    """Handle a candidate response during skill assessment."""
    skill_name = state.skills_to_assess[state.current_skill_index]
    skill_state = state.skill_states[skill_name]

    candidate_claim, resume_evidence = get_resume_evidence_for_skill(
        skill_name, state.resume_profile.skills_claimed
    )

    expected_level = "intermediate"
    for jd_skill in state.jd_profile.required_skills:
        if jd_skill.skill_name.lower() == skill_name.lower():
            expected_level = jd_skill.expected_proficiency.value
            break

    reply, updated_skill_state = await asyncio.to_thread(
        get_next_assessor_message,
        skill_state, candidate_claim, resume_evidence, expected_level, user_message
    )

    state.skill_states[skill_name] = updated_skill_state

    # Check if this skill assessment is done
    if updated_skill_state.is_complete:
        # Move to transition (or wrap-up if last skill)
        is_last_skill = state.current_skill_index >= len(state.skills_to_assess) - 1
        if is_last_skill:
            state.stage = SessionStage.WRAP_UP
            # Append completion reply, then add wrap-up message
            wrap_up = _generate_orchestrator_message(state)
            state.stage = SessionStage.SCORING
            # Combine the assessor's closing line + wrap-up
            full_reply = f"{reply}\n\n{wrap_up}"
            return full_reply, state
        else:
            state.stage = SessionStage.TRANSITION
            transition_msg = _generate_orchestrator_message(state)
            full_reply = f"{reply}\n\n{transition_msg}"
            return full_reply, state

    return reply, state


# ─────────────────────────────────────────────────────────────────────────────
# GET /report — Score all skills, generate learning plan, return full report
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/report/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str):
    """
    Step 3: Score all assessed skills and generate the personalized learning plan.
    Can be polled — returns cached report if already generated.
    """
    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if state.stage not in (SessionStage.SCORING, SessionStage.REPORT):
        raise HTTPException(
            status_code=400,
            detail=f"Assessment not yet complete. Current stage: {state.stage.value}"
        )

    # Return cached report if already generated
    if state.stage == SessionStage.REPORT and state.learning_plan:
        return _build_report_response(state)

    # ── Score all completed skill assessments ────────────────────────────
    scores = []
    for skill_name, skill_state in state.skill_states.items():
        candidate_claim, resume_evidence = get_resume_evidence_for_skill(
            skill_name, state.resume_profile.skills_claimed
        )
        expected_level = "intermediate"
        for jd_skill in state.jd_profile.required_skills:
            if jd_skill.skill_name.lower() == skill_name.lower():
                expected_level = jd_skill.expected_proficiency.value
                break

        score = await asyncio.to_thread(
            score_skill,
            skill_name, skill_state.conversation, resume_evidence, expected_level
        )
        scores.append(score)
        skill_state.score = score

    state.final_scores = scores

    # ── Generate learning plan ───────────────────────────────────────────
    try:
        plan = await asyncio.to_thread(
            generate_learning_plan,
            state.resume_profile, state.jd_profile, scores, state.gap_analysis
        )
        state.learning_plan = plan
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Learning plan generation failed: {str(e)}")

    state.stage = SessionStage.REPORT
    save_session(state)

    return _build_report_response(state)


def _build_report_response(state: SessionState) -> ReportResponse:
    return ReportResponse(
        session_id=state.session_id,
        candidate_name=state.resume_profile.candidate_name,
        target_role=state.jd_profile.job_title,
        overall_match_score=state.gap_analysis.overall_match_score,
        scores=state.final_scores,
        learning_plan=state.learning_plan,
        gap_analysis=state.gap_analysis,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /session/{session_id} — Get session status
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/session/{session_id}")
def get_session_status(session_id: str):
    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return {
        "session_id": state.session_id,
        "stage": state.stage.value,
        "candidate_name": state.resume_profile.candidate_name if state.resume_profile else None,
        "target_role": state.jd_profile.job_title if state.jd_profile else None,
        "skills_to_assess": state.skills_to_assess,
        "current_skill_index": state.current_skill_index,
        "match_score": state.gap_analysis.overall_match_score if state.gap_analysis else None,
        "chat_history": [m.model_dump() for m in state.chat_history],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator message generator (PROMPT 7)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_orchestrator_message(state: SessionState) -> str:
    """Generate the appropriate orchestrator message for the current stage."""
    try:
        previous_skill = ""
        previous_strength = ""
        if state.current_skill_index > 0 and state.final_scores:
            prev_skill_name = state.skills_to_assess[state.current_skill_index - 1]
            prev_score = next(
                (s for s in state.final_scores if s.skill_name == prev_skill_name), None
            )
            if prev_score and prev_score.strengths_observed:
                previous_skill = prev_skill_name
                previous_strength = prev_score.strengths_observed[0]

        prompt_content = ORCHESTRATOR_PROMPT.format(
            current_stage=state.stage.value,
            candidate_name=state.resume_profile.candidate_name if state.resume_profile else "there",
            target_role=state.jd_profile.job_title if state.jd_profile else "this role",
            skills_list=", ".join(state.skills_to_assess),
            current_skill_index=state.current_skill_index,
            previous_skill=previous_skill or "N/A",
            previous_strength=previous_strength or "N/A",
            results_so_far=json.dumps([s.model_dump() for s in state.final_scores], indent=2)
            if state.final_scores else "[]",
        )

        return call_llm("You are a warm, helpful assessment orchestrator.", prompt_content, max_tokens=256)

    except Exception:
        # Hardcoded fallbacks if orchestrator call fails
        if state.stage == SessionStage.WELCOME:
            name = state.resume_profile.candidate_name if state.resume_profile else "there"
            role = state.jd_profile.job_title if state.jd_profile else "this role"
            skills = ", ".join(state.skills_to_assess)
            return (
                f"Hi {name}! 👋 I'm your Skill Assessment Agent. I've reviewed your resume and the "
                f"{role} job description. I'll have a short conversation with you about {len(state.skills_to_assess)} "
                f"skills: {skills}. This isn't a test — it's to help me build you a truly personalized "
                f"learning plan. Ready to start?"
            )
        elif state.stage == SessionStage.TRANSITION:
            next_skill = state.skills_to_assess[state.current_skill_index] if state.current_skill_index < len(state.skills_to_assess) else "the next topic"
            return f"Great, that's very helpful! Let's shift over to {next_skill} now."
        elif state.stage == SessionStage.WRAP_UP:
            return (
                "That's everything I needed! You shared some really insightful answers. "
                "Give me a moment to process your results and build your personalized learning plan... 🎯"
            )
        return "Let's continue! Ready when you are."
