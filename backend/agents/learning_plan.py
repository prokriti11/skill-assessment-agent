# learning_plan.py
# Agent 6: Generates a personalized learning plan using all assessment data.

import json
from backend.models.schemas import ResumeProfile, JDProfile, GapAnalysis, SkillScore, LearningPlan
from backend.prompts.all_prompts import LEARNING_PLAN_PROMPT
from backend.utils.llm_client import call_llm


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def generate_learning_plan(
    resume: ResumeProfile,
    jd: JDProfile,
    scores: list[SkillScore],
    gap_analysis: GapAnalysis,
) -> LearningPlan:
    scores_data = [s.model_dump() for s in scores]

    prompt_content = LEARNING_PLAN_PROMPT.format(
        candidate_profile=resume.model_dump_json(indent=2),
        job_profile=jd.model_dump_json(indent=2),
        skill_scores=json.dumps(scores_data, indent=2),
        gap_analysis=gap_analysis.model_dump_json(indent=2),
    )

    try:
        raw = call_llm("You are a world-class learning designer. Return only valid JSON.", prompt_content, max_tokens=8192)
        raw = _strip_fences(raw)
        return LearningPlan(**json.loads(raw))
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON for learning plan: {e}")
    except Exception as e:
        raise ValueError(f"Learning plan generation failed: {e}")
