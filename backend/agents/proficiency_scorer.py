# proficiency_scorer.py
# Agent 5: Scores a candidate's proficiency based on conversation transcript.

import json
from backend.models.schemas import SkillScore, ConversationMessage
from backend.prompts.all_prompts import PROFICIENCY_SCORER_PROMPT
from backend.utils.llm_client import call_llm


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def score_skill(
    skill_name: str,
    conversation: list[ConversationMessage],
    resume_evidence: str,
    expected_level: str,
) -> SkillScore:
    transcript_lines = []
    for msg in conversation:
        label = "Assessor" if msg.role == "assistant" else "Candidate"
        transcript_lines.append(f"{label}: {msg.content}")
    transcript = "\n".join(transcript_lines)

    if not transcript.strip():
        return _fallback_score(skill_name, "No conversation recorded.")

    prompt = PROFICIENCY_SCORER_PROMPT.format(
        skill_name=skill_name,
        expected_level=expected_level,
        resume_evidence=resume_evidence,
        conversation_transcript=transcript,
    )

    try:
        raw = call_llm("You are an expert skill evaluator. Return only valid JSON.", prompt, max_tokens=1024)
        raw = _strip_fences(raw)
        return SkillScore(**json.loads(raw))
    except json.JSONDecodeError as e:
        return _fallback_score(skill_name, f"Parse error: {e}")
    except Exception as e:
        return _fallback_score(skill_name, f"Error: {e}")


def _fallback_score(skill_name: str, reason: str) -> SkillScore:
    return SkillScore(
        skill_name=skill_name,
        proficiency_score=3,
        proficiency_label="beginner",
        confidence="low",
        score_reasoning=f"Score could not be fully determined. {reason}",
        strengths_observed=["Assessment data incomplete"],
        gaps_observed=["Could not evaluate fully"],
        claim_accuracy="accurate",
        ready_for_role="with_upskilling",
        estimated_gap_weeks=6,
    )
