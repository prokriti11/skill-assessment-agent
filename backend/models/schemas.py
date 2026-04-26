# schemas.py
# Pydantic v2 data models for all agent inputs, outputs, and session state.
# These models are the single source of truth for data structures across the entire app.

from __future__ import annotations
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class SeniorityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"

class Importance(str, Enum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"

class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class Recency(str, Enum):
    CURRENT = "current"
    RECENT = "recent"
    DATED = "dated"
    OLD = "old"

class CandidateStatus(str, Enum):
    STRONG_MATCH = "strong_match"
    PARTIAL_MATCH = "partial_match"
    GAP = "gap"
    UNVERIFIED_CLAIM = "unverified_claim"
    NOT_PRESENT = "not_present"

class GapSeverity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"

class SessionStage(str, Enum):
    UPLOAD = "upload"
    PARSING = "parsing"
    WELCOME = "welcome"
    CONFIRM_SKILLS = "confirm_skills"
    ASSESSING = "assessing"
    TRANSITION = "transition"
    WRAP_UP = "wrap_up"
    SCORING = "scoring"
    REPORT = "report"

class ReadinessLevel(str, Enum):
    READY = "ready"
    ONE_TO_THREE = "1-3 months"
    THREE_TO_SIX = "3-6 months"
    SIX_TO_TWELVE = "6-12 months"
    TWELVE_PLUS = "12+ months"


# ─── JD Profile ───────────────────────────────────────────────────────────────

class JDSkill(BaseModel):
    skill_name: str
    category: SkillCategory
    importance: Importance
    expected_proficiency: ProficiencyLevel
    context: str

class JDProfile(BaseModel):
    job_title: str
    seniority_level: SeniorityLevel
    domain: str
    required_skills: list[JDSkill]
    responsibilities: list[str]
    years_of_experience_required: Optional[float] = None
    industry_context: str


# ─── Resume Profile ───────────────────────────────────────────────────────────

class Education(BaseModel):
    degree: str
    field: str
    institution: str
    year: Optional[int] = None

class ClaimedSkill(BaseModel):
    skill_name: str
    category: SkillCategory
    evidence: str
    estimated_years: Optional[float] = None
    recency: Recency

class NotableProject(BaseModel):
    name: str
    description: str
    skills_demonstrated: list[str]
    impact: Optional[str] = None

class ResumeProfile(BaseModel):
    candidate_name: str
    total_years_experience: float
    current_role: str
    education: list[Education]
    skills_claimed: list[ClaimedSkill]
    notable_projects: list[NotableProject]
    career_trajectory: str


# ─── Gap Analysis ─────────────────────────────────────────────────────────────

class SkillGapEntry(BaseModel):
    skill_name: str
    jd_importance: Importance
    jd_expected_level: ProficiencyLevel
    candidate_status: CandidateStatus
    resume_evidence: Optional[str] = None
    assessment_needed: bool
    assessment_priority: str  # "high" | "medium" | "low"
    gap_severity: GapSeverity

class AdjacentSkillOpportunity(BaseModel):
    gap_skill: str
    candidate_has: str
    bridge_reasoning: str

class GapAnalysis(BaseModel):
    overall_match_score: int = Field(ge=0, le=100)
    match_summary: str
    skill_analysis: list[SkillGapEntry]
    skills_to_assess: list[str]
    strengths: list[str]
    critical_gaps: list[str]
    adjacent_skills_opportunity: list[AdjacentSkillOpportunity]


# ─── Skill Score ──────────────────────────────────────────────────────────────

class SkillScore(BaseModel):
    skill_name: str
    proficiency_score: int = Field(ge=0, le=10)
    proficiency_label: str  # none | novice | beginner | intermediate | advanced | expert
    confidence: str  # low | medium | high
    score_reasoning: str
    strengths_observed: list[str]
    gaps_observed: list[str]
    claim_accuracy: str  # overclaimed | accurate | underclaimed
    ready_for_role: str  # yes | with_upskilling | no
    estimated_gap_weeks: int = Field(ge=0)


# ─── Learning Plan ────────────────────────────────────────────────────────────

class LearningResource(BaseModel):
    title: str
    type: str  # course | book | documentation | project | video | practice_platform
    url: Optional[str] = None
    provider: str
    estimated_hours: int
    why_this_resource: str

class SkillLearningItem(BaseModel):
    skill_name: str
    current_level: str
    target_level: str
    why_prioritized: str
    weekly_commitment_hours: int
    resources: list[LearningResource]
    milestone: str

class LearningPhase(BaseModel):
    phase_number: int
    phase_name: str
    duration_weeks: int
    focus: str
    skills: list[SkillLearningItem]

class QuickWin(BaseModel):
    action: str
    impact: str

class SkipItem(BaseModel):
    skill_name: str
    reason: str

class LearningPlan(BaseModel):
    candidate_name: str
    target_role: str
    readiness_level: str
    overall_recommendation: str
    learning_phases: list[LearningPhase]
    quick_wins: list[QuickWin]
    skills_to_skip_for_now: list[SkipItem]
    motivational_note: str


# ─── Session State ────────────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class SkillAssessmentState(BaseModel):
    skill_name: str
    exchange_count: int = 0
    conversation: list[ConversationMessage] = []
    score: Optional[SkillScore] = None
    is_complete: bool = False

class SessionState(BaseModel):
    session_id: str
    stage: SessionStage = SessionStage.UPLOAD
    jd_text: str = ""
    jd_profile: Optional[JDProfile] = None
    resume_text: str = ""
    resume_profile: Optional[ResumeProfile] = None
    gap_analysis: Optional[GapAnalysis] = None
    skills_to_assess: list[str] = []
    current_skill_index: int = 0
    skill_states: dict[str, SkillAssessmentState] = {}
    final_scores: list[SkillScore] = []
    learning_plan: Optional[LearningPlan] = None
    chat_history: list[ConversationMessage] = []  # full visible chat


# ─── API Request/Response Models ──────────────────────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    match_score: int
    skills_to_assess: list[str]
    welcome_message: str
    stage: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    stage: str
    current_skill: Optional[str] = None
    skill_index: int = 0
    total_skills: int = 0
    is_complete: bool = False

class ReportResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    overall_match_score: int
    scores: list[SkillScore]
    learning_plan: LearningPlan
    gap_analysis: GapAnalysis
