# Demo Script — SkillSense AI (4 Minutes)
## Catalyst Hackathon Demo Video

**Recording setup**: Screen record at 1080p. Have both browser tabs open: Streamlit (localhost:8501) and the sample files ready. Use the sample_resume.txt and sample_jd.txt from the repo.

---

## 0:00–0:30 — PROBLEM STATEMENT (Voice only, show a simple slide or just the README)

**Say:**
> "Every year, millions of developers apply for jobs they're 60 to 80 percent qualified for. They get rejected — not because they can't do the job — but because they don't know exactly which skills to level up, and no one tells them.
>
> Generic learning platforms give you the same Python course whether you're a senior engineer with 4 years of experience or a student just starting out.
>
> SkillSense AI changes that. It reads your resume, reads the job description, has an intelligent conversation with you to assess where you actually are — and then builds you a hyper-personalized, phased learning plan. Not a generic roadmap. Your roadmap."

---

## 0:30–1:00 — UPLOAD PHASE (Switch to Streamlit browser tab)

**Say:**
> "Let me show you how it works. I'm going to use a sample resume from a 4-year backend engineer named Arjun, who's applying to a Senior Backend Engineer role at a fintech startup."

**Action**: 
1. Click the file uploader → upload `samples/sample_resume.txt`  
2. Paste the contents of `samples/sample_jd.txt` into the JD text area
3. Show the resume briefly — scroll through it — then show the JD

**Say:**
> "Arjun has solid Python and PostgreSQL experience — he's built real systems. But the role requires distributed systems knowledge, Kafka, and AWS cloud services — areas where he's more junior."

**Action**: 
4. Click **"🚀 Start Assessment"**
5. A spinner appears — let it run

**Say (while spinner is running):**
> "Behind the scenes, three agents are running in parallel: one parsing the resume, one parsing the JD, and then a gap analyzer comparing the two — all powered by Claude claude-sonnet-4-20250514."

---

## 1:00–1:30 — WELCOME + CONFIRM SKILLS (The chat UI appears)

**Action**: The welcome message appears from the assistant.

**Say:**
> "The agent introduces itself, lists the skills it'll assess — and importantly, it explains this is not a test. The tone is collaborative, not interrogative."

**Action**: 
1. Read the welcome message aloud (or paraphrase it)
2. The sidebar now shows: Arjun's name, target role, match score, and the list of skills to be assessed
3. Type **"Yes, ready!"** and hit Enter

**Say:**
> "We're assessing 5 skills: PostgreSQL, Distributed Systems, Redis, System Design, and Docker."

---

## 1:30–3:00 — ASSESSMENT CONVERSATION (This is the money shot)

**For PostgreSQL (Skill 1):**

Agent asks something like: *"Can you tell me what you understand by PostgreSQL query optimization — and when you'd reach for it?"*

**Type this answer:**
> "Sure — I use EXPLAIN ANALYZE to look at query plans. In my last job I had a query that was doing a sequential scan on a 5M row orders table. I added a composite index on (user_id, created_at) and got it from 800ms down to 90ms."

**Say (while typing):**
> "I'm giving a real, specific answer — the kind that demonstrates genuine practical experience."

Agent follows up, asks about a specific scenario or tradeoff.

**Type:**
> "One thing I learned: indexes have a cost on writes. For our insert-heavy tables I was careful about how many indexes I added — we profiled write throughput before and after."

**Say:**
> "Notice how the agent probes deeper — it's not a checkbox, it's a real conversation."

---

**For Distributed Systems (Skill 2):**

Agent asks: *"Can you explain what eventual consistency means and when you'd design a system around it?"*

**Type:**
> "Eventual consistency means nodes may have different data at a moment in time but will converge given no new writes. I've read about it but haven't built a fully distributed system from scratch — in my current role we use PostgreSQL transactions for consistency."

**Say:**
> "I'm being honest here — showing a partial gap. The agent will handle this gracefully."

Agent follows up warmly — notice it doesn't penalize honesty.

**Type:**
> "I understand CAP theorem at a conceptual level — like, you can't have consistency, availability, and partition tolerance all at once. For a payments system I'd probably prioritize CP over AP."

---

## 3:00–3:45 — REPORT PHASE (The learning plan appears)

After the last skill, the agent wraps up. Streamlit auto-fetches the report.

**Say:**
> "After all 5 skills are assessed, the scoring agent processes each transcript — and the learning plan generator creates a personalized, phased roadmap."

**Show on screen as you narrate:**

1. **Overall match score** — "Arjun's profile is a 62% match — solid foundation, real gaps."

2. **Skill scores** — Click through each card:
   > "PostgreSQL: 7/10 — solid, with real evidence. Distributed Systems: 4/10 — conceptual but no production experience. This is honest scoring."

3. **Phase 1 of the learning plan** — Expand it:
   > "Phase 1 is 4 weeks, focused on Distributed Systems and Kafka. Notice the resources are real — 'Designing Data-Intensive Applications' by Kleppmann, Apache Kafka's official quickstart, and a project milestone: build a producer-consumer pipeline."

4. **Quick Wins section:**
   > "And here are three things Arjun can do in the next 48 hours to get started right now."

5. **Download button** — Click it:
   > "The entire plan is downloadable as JSON — or Markdown — so Arjun can take it anywhere."

---

## 3:45–4:00 — CLOSING IMPACT STATEMENT

**Say (face cam or voice over):**
> "SkillSense AI isn't a quiz. It's not a course catalog. It's a personalized coaching conversation that meets candidates exactly where they are — and builds them a realistic, actionable path to where they want to be.
>
> For a hackathon, we built this in under 18 hours using Claude claude-sonnet-4-20250514, FastAPI, and Streamlit. The same architecture can scale to career platforms, engineering bootcamps, and enterprise L&D teams.
>
> Thank you."

---

## Tips for a Great Recording

- **Don't rush the upload phase** — the 30-second spinner is a good moment to explain the architecture
- **Type answers slowly** so viewers can read them
- **Pre-warm your Render deployment** if using the hosted version (hit /health 1 min before recording)
- **Use the sample data** — it's calibrated to produce an impressive, balanced output
- **Show the sidebar** — the skill progress tracker is a great visual
- **Zoom in on the score cards** when showing the report

---

## Sample Answers to Use for Maximum Demo Impact

| Skill | Q Type | Use This Answer |
|---|---|---|
| PostgreSQL | Conceptual | "Query optimization using EXPLAIN ANALYZE — I've optimized joins on 5M+ row tables by redesigning index strategies" |
| Distributed Systems | Applied | "I understand CAP theorem and eventual consistency conceptually; in practice I've relied on PostgreSQL for strong consistency but I've read DDIA" |
| Redis | Applied | "I use Redis for caching and implemented a TTL-based invalidation strategy that cut DB read load by 40%; also used it for a rate limiter with token buckets" |
| System Design | Depth | "I'd horizontally scale the API layer with a load balancer, use read replicas for PostgreSQL, and introduce async processing via Celery for non-critical paths" |
| Docker | Conceptual | "I containerize all services with Docker; use multi-stage builds to reduce image size; maintain docker-compose for local dev" |
