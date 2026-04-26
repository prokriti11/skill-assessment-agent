# resume_parser.py
# Agent 2: Parses extracted resume text into a structured ResumeProfile.

import json
from backend.models.schemas import ResumeProfile
from backend.prompts.all_prompts import RESUME_PARSER_PROMPT
from backend.utils.llm_client import call_llm


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def parse_resume(resume_text: str) -> ResumeProfile:
    if not resume_text or len(resume_text.strip()) < 100:
        raise ValueError("Resume text is too short or empty.")

    user_message = f"""Parse the following resume and return the structured JSON as instructed:

---RESUME START---
{resume_text.strip()}
---RESUME END---"""

    try:
        raw = call_llm(RESUME_PARSER_PROMPT, user_message, max_tokens=4096)
        raw = _strip_fences(raw)
        return ResumeProfile(**json.loads(raw))
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON for resume parsing: {e}")
    except Exception as e:
        raise ValueError(f"Resume parsing failed: {e}")
