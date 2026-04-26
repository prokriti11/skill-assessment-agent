# jd_parser.py
# Agent 1: Parses a raw Job Description string into a structured JDProfile.

import json
from backend.models.schemas import JDProfile
from backend.prompts.all_prompts import JD_PARSER_PROMPT
from backend.utils.llm_client import call_llm


def parse_jd(jd_text: str) -> JDProfile:
    if not jd_text or len(jd_text.strip()) < 50:
        raise ValueError("Job description is too short or empty.")

    user_message = f"""Parse the following Job Description and return the structured JSON as instructed:

---JOB DESCRIPTION START---
{jd_text.strip()}
---JOB DESCRIPTION END---"""

    try:
        raw = call_llm(JD_PARSER_PROMPT, user_message, max_tokens=4096)
        raw = _strip_fences(raw)
        return JDProfile(**json.loads(raw))
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON for JD parsing: {e}")
    except Exception as e:
        raise ValueError(f"JD parsing failed: {e}")


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
