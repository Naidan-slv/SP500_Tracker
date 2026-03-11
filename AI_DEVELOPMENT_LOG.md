# AI Development Log
### Stock Intelligence API — COMP3011 Coursework 1
**Student:** Naidan Salvador  
**Module:** Web Services and Web Data (COMP3011)  
**Submission Deadline:** 13 March 2026  
**Oral Examination:** Week commencing 23 March 2026  

---

## GenAI Tools Used

| Tool | Purpose |
|---|---|
| GitHub Copilot (Claude Sonnet 4.6) | Primary development assistant — planning, architecture, code generation, debugging, and review |

---

## How This Log Works

This document tracks every meaningful development session, recording:
- What was built or decided
- What was asked of the AI and why
- What the AI produced
- What I changed, overrode, or questioned
- Personal reflections on the process

This serves as the GenAI declaration required by the COMP3011 brief and as the foundation for the technical report's AI usage section.

---

## Development Log

---

### Entry 001 — Project Scoping and Planning
**Date:** 11 March 2026  
**Commit(s):** Initial planning phase  

#### What Was Done
- Defined the full project concept: a Stock Intelligence API combining historical OHLCV data, portfolio management, analytics, live quotes, and news contextualisation
- Discussed the assignment brief requirements and mapped them to the project scope
- Agreed on the core tech stack
- Decided to maintain two documentation files: `README.md` for technical setup and this log for AI usage tracking

#### What I Asked the AI
- Provided the full master prompt describing the project vision and asked for confirmation of understanding
- Asked the AI to assess whether the project satisfies the assignment brief's minimum requirements and grade band criteria
- Asked for tech stack recommendations with justifications
- Asked whether two separate documentation files made sense for the project

#### What the AI Produced
- A structured breakdown of the project understanding across all layers (data, ingestion, analytics, enrichment, API)
- A mapping of the project against the brief's CRUD and endpoint requirements, confirming it exceeds the pass criteria and targets the 70–89 band
- A full tech stack recommendation: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pydantic, pandas, httpx, Finnhub, Render for deployment
- Justification for PostgreSQL over SQLite/MongoDB given the relational nature of the data
- Recommendation for Render as the deployment platform due to its free PostgreSQL tier and GitHub auto-deploy

#### My Decisions and Overrides
- Agreed with the full stack recommendation — it aligns with what the module has covered and extends it appropriately
- Chose to use Finnhub as the external API provider based on the AI's recommendation of its combined quote/profile/news support on a free tier
- Decided to keep the two-file documentation structure as it cleanly separates technical setup from AI usage evidence

#### Reflections
The planning phase was entirely AI-assisted in terms of structuring the project vision and validating it against the brief. The AI helped surface trade-offs I had not considered (e.g. SQLite limitations at deployment, Render vs PythonAnywhere). My role in this phase was to evaluate the recommendations critically and make final decisions about scope and tooling.

---

### Entry 002 — *(To be completed)*
**Date:**  
**Commit(s):**  

#### What Was Done

#### What I Asked the AI

#### What the AI Produced

#### My Decisions and Overrides

#### Reflections

---

*This log will be updated after each meaningful development session or commit batch.*
