# gap_analyzer.py
# Agent 3: Compares JDProfile vs ResumeProfile to produce a GapAnalysis.

import json
from backend.models.schemas import JDProfile, ResumeProfile, GapAnalysis
from backend.prompts.all_prompts import GAP_ANALYZER_PROMPT
from backend.utils.llm_client import call_llm


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def analyze_gaps(jd: JDProfile, resume: ResumeProfile) -> GapAnalysis:
    user_message = f"""Analyze the gap between this candidate and the job requirements.

JOB DESCRIPTION PROFILE:
{jd.model_dump_json(indent=2)}

CANDIDATE RESUME PROFILE:
{resume.model_dump_json(indent=2)}

Return the gap analysis JSON as instructed."""

    try:
        raw = call_llm(GAP_ANALYZER_PROMPT, user_message, max_tokens=4096)
        raw = _strip_fences(raw)
        data = json.loads(raw)
        if "skills_to_assess" in data and len(data["skills_to_assess"]) > 6:
            data["skills_to_assess"] = data["skills_to_assess"][:6]
        return GapAnalysis(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON for gap analysis: {e}")
    except Exception as e:
        raise ValueError(f"Gap analysis failed: {e}")
