# SkillSense AI — Skill Assessment & Personalized Learning Plan Agent

> **Built for Catalyst Hackathon · Deadline: April 27, 2026**

SkillSense AI is a multi-agent conversational system that parses a candidate's resume and a job description, conducts a warm skill assessment interview powered by Claude claude-sonnet-4-20250514, scores proficiency per skill, and generates a hyper-personalized, phased learning plan — all in one seamless flow.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SKILLSENSE AI PIPELINE                       │
│                                                                     │
│  ┌──────────┐    ┌────────────────────────────────────────────┐    │
│  │ Streamlit │    │              FastAPI Backend               │    │
│  │ Frontend  │◄──►│                                            │    │
│  │           │    │  POST /upload  POST /chat  GET /report     │    │
│  └──────────┘    └──────────────────┬─────────────────────────┘    │
│                                     │                               │
│         ┌───────────────────────────▼──────────────────────┐       │
│         │              AGENT PIPELINE                       │       │
│         │                                                   │       │
│  Resume ──► [Agent 1: PDF Extractor]                        │       │
│  PDF        [Agent 2: Resume Parser] ──► ResumeProfile      │       │
│                                                             │       │
│  JD Text ──► [Agent 3: JD Parser] ──► JDProfile            │       │
│                                                             │       │
│         [Agent 4: Gap Analyzer] ◄── JDProfile + Resume     │       │
│                    │                                        │       │
│                    ▼                                        │       │
│             GapAnalysis (skills to assess, 1-6)            │       │
│                    │                                        │       │
│         ┌──────────▼──────────────────────────────┐        │       │
│         │     STATE MACHINE (Orchestrator)         │        │       │
│         │  WELCOME → CONFIRM → ASSESS_N →          │        │       │
│         │  TRANSITION → WRAP_UP → SCORING          │        │       │
│         └──────────┬──────────────────────────────┘        │       │
│                    │                                        │       │
│         [Agent 5: Skill Assessor] (multi-turn, per skill)  │       │
│                    │                                        │       │
│         [Agent 6: Proficiency Scorer] (post-assessment)    │       │
│                    │                                        │       │
│         [Agent 7: Learning Plan Generator] ──► LearningPlan│       │
│         └───────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **LLM** | Claude claude-sonnet-4-20250514 | Best multi-turn reasoning, JSON reliability |
| **Backend** | Python + FastAPI | Async, fast, clean type hints |
| **Frontend** | Streamlit | Fastest to build, great for demos |
| **PDF Parsing** | pdfplumber | Best multi-column layout support |
| **Orchestration** | Custom state machine | No LangChain overhead |
| **Storage** | In-memory (session dict) | Sufficient for hackathon |
| **Validation** | Pydantic v2 | All agent I/O is type-safe |

---

## Project Structure

```
skill-assessment-agent/
├── backend/
│   ├── main.py                   # FastAPI app — orchestrator + all endpoints
│   ├── agents/
│   │   ├── jd_parser.py          # Agent 1: JD → structured JSON
│   │   ├── resume_parser.py      # Agent 2: Resume text → structured JSON
│   │   ├── gap_analyzer.py       # Agent 3: JD + Resume → gap analysis
│   │   ├── skill_assessor.py     # Agent 4: Multi-turn conversational assessor
│   │   ├── proficiency_scorer.py # Agent 5: Transcript → proficiency score
│   │   └── learning_plan.py      # Agent 6: All data → personalized plan
│   ├── models/
│   │   └── schemas.py            # Pydantic models for all data structures
│   ├── prompts/
│   │   └── all_prompts.py        # All 7 Claude system prompts
│   └── utils/
│       ├── pdf_extractor.py      # pdfplumber PDF → text
│       └── session_store.py      # In-memory session management
├── frontend/
│   └── app.py                    # Streamlit 3-phase UI
├── samples/
│   ├── sample_jd.txt             # Senior Backend Engineer JD
│   ├── sample_resume.txt         # 4-year backend engineer resume
│   └── sample_output.json        # Expected output for sample inputs
├── .env.example                  # Environment variable template
├── requirements.txt
└── README.md
```

---

## Local Setup (Fresh Machine)

### Prerequisites
- Python 3.11+
- pip
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Step 1: Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/skill-assessment-agent.git
cd skill-assessment-agent
```

### Step 2: Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
BACKEND_URL=http://localhost:8000
```

### Step 5: Run the backend

```bash
uvicorn backend.main:app --reload
```

You should see:
```
✅ Skill Assessment Agent API is starting up...
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 6: Run the frontend (new terminal)

```bash
# Activate venv again in the new terminal
source venv/bin/activate  # or venv\Scripts\activate on Windows

streamlit run frontend/app.py
```

Streamlit will open at `http://localhost:8501` automatically.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | — | Your Anthropic API key |
| `BACKEND_URL` | No | `http://localhost:8000` | URL of the FastAPI backend |

---

## How to Use

1. **Upload**: In the Streamlit UI, upload your resume PDF and paste the job description text
2. **Assess**: The agent will analyze both documents and start a warm conversational assessment (3–6 skills, ~4 exchanges each)
3. **Report**: After the conversation, get your personalized learning plan with:
   - Skill scores (0–10) with reasoning
   - Phased learning plan (2–3 phases, real resources)
   - 48-hour quick wins
   - Download as JSON or Markdown

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload resume + JD, start session |
| `POST` | `/chat` | Send message, get response |
| `GET` | `/report/{session_id}` | Get full assessment report |
| `GET` | `/session/{session_id}` | Get session status |

### Example: Upload

```bash
curl -X POST http://localhost:8000/upload \
  -F "resume=@samples/sample_resume.txt" \
  -F "jd_text=$(cat samples/sample_jd.txt)"
```

### Example: Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "I use Redis for caching — specifically TTL-based invalidation"}'
```

---

## Scoring Logic

```
Proficiency Score (0–10):
  ├── Conceptual accuracy:     40% weight
  ├── Applied experience:      40% weight
  └── Depth / edge cases:      20% weight

Gap Severity Mapping:
  ├── critical: must_have skill, score < 4
  ├── moderate: must_have skill, score 4–6
  ├── minor:    nice_to_have OR score 6–7
  └── none:     score ≥ 8

Readiness Calculation:
  └── Sum of (estimated_gap_weeks × importance_weight)
      must_have weight = 2.0
      nice_to_have weight = 0.5

      Total < 4 weeks   → "ready"
      Total 4–12 weeks  → "1-3 months"
      Total 12–24 weeks → "3-6 months"
      Total 24–48 weeks → "6-12 months"
      Total 48+ weeks   → "12+ months"
```

---

## Sample Input → Output

**Input**: `samples/sample_resume.txt` (4-year backend engineer, Arjun Mehta) + `samples/sample_jd.txt` (Senior Backend Engineer, TechScale)

**Expected Output Summary**:
- Match Score: ~62%
- Skills Assessed: PostgreSQL, Distributed Systems, Redis, System Design, Docker, Kafka
- Readiness: 3–6 months
- Phase 1: Distributed Systems + Kafka (4 weeks)
- Phase 2: AWS Cloud Services + K8s basics (4 weeks)
- Quick Wins: Read "Designing Data-Intensive Applications" Ch.5, set up a Kafka local cluster

See `samples/sample_output.json` for the full expected JSON output.

---

## Demo Video

🎥 [Watch Demo](YOUR_LOOM_URL_HERE)

## Live Demo

🚀 [Try It Live](YOUR_RENDER_URL_HERE)

---

## Architecture Decisions

- **No LangChain**: Custom state machine gives full control, easier to debug under hackathon pressure
- **Pydantic v2**: All LLM outputs are validated against strict schemas — prevents silent failures
- **Parallel parsing**: JD + resume are parsed concurrently with `asyncio.gather` for speed
- **Graceful fallbacks**: Every Claude call has try/except — the app never crashes on LLM errors
- **Session TTL**: Sessions expire after 4 hours — memory-safe for demo use

---

*Built by [Your Name] for Catalyst Hackathon 2026*
