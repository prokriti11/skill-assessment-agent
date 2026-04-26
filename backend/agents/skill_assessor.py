# skill_assessor.py
# Agent 4: Multi-turn conversational skill assessor using Groq.

import os
from backend.models.schemas import ConversationMessage, SkillAssessmentState, ClaimedSkill
from backend.prompts.all_prompts import SKILL_ASSESSOR_SYSTEM_PROMPT
from backend.utils.llm_client import call_llm_with_history

COMPLETION_MARKERS = [
    "let's move on",
    "that's really helpful",
    "i have a clear picture",
    "clear picture of your",
    "let's move on to",
]
MAX_EXCHANGES_PER_SKILL = 4


def get_next_assessor_message(
    skill_state: SkillAssessmentState,
    candidate_claim: str,
    resume_evidence: str,
    expected_level: str,
    user_message: str | None = None,
) -> tuple[str, SkillAssessmentState]:
    skill_name = skill_state.skill_name

    system_prompt = SKILL_ASSESSOR_SYSTEM_PROMPT.format(
        skill_name=skill_name,
        expected_level=expected_level,
        candidate_claim=candidate_claim,
        resume_evidence=resume_evidence,
    )

    messages = [{"role": m.role, "content": m.content} for m in skill_state.conversation]

    if user_message:
        if len(user_message.strip().split()) < 10 and skill_state.exchange_count > 0:
            system_prompt += f"\n\nNOTE: The candidate gave a very brief answer: '{user_message}'. Gently invite elaboration before moving on."
        messages.append({"role": "user", "content": user_message})
    else:
        messages.append({
            "role": "user",
            "content": f"Please begin the assessment for {skill_name}. Ask your first question."
        })

    try:
        reply = call_llm_with_history(system_prompt, messages, max_tokens=512)
    except Exception:
        reply = f"Let's talk about {skill_name} — can you tell me how you've used it in your work?"

    if user_message:
        skill_state.conversation.append(ConversationMessage(role="user", content=user_message))
    else:
        skill_state.conversation.append(ConversationMessage(
            role="user",
            content=f"Please begin the assessment for {skill_name}. Ask your first question."
        ))

    skill_state.conversation.append(ConversationMessage(role="assistant", content=reply))
    skill_state.exchange_count += 1
    skill_state.is_complete = _check_completion(reply) or skill_state.exchange_count >= MAX_EXCHANGES_PER_SKILL

    return reply, skill_state


def _check_completion(reply: str) -> bool:
    return any(marker in reply.lower() for marker in COMPLETION_MARKERS)


def get_resume_evidence_for_skill(skill_name: str, resume_skills: list[ClaimedSkill]) -> tuple[str, str]:
    skill_lower = skill_name.lower()
    for claimed in resume_skills:
        if claimed.skill_name.lower() == skill_lower or skill_lower in claimed.skill_name.lower():
            claim = f"{claimed.skill_name} ({claimed.recency.value}, ~{claimed.estimated_years or 'unknown'} years)"
            return claim, claimed.evidence or "No specific evidence mentioned"
    return "Not mentioned on resume", "No evidence found in resume"
