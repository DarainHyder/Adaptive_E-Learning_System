---
title: Adaptive Elearning Backend
emoji: 🧠
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Adaptive E-Learning System

Adaptive tutoring that models what each learner knows, teaches at their level, and brings topics
back just before they are forgotten.

- **Frontend**: React + Vite + Tailwind (Vercel), at https://adaptive-e-learning-system.vercel.app
- **Backend**: Flask API on a Hugging Face Space (Docker)
- **Agents**: LangGraph multi-agent graph with LangChain structured outputs (Gemini)
- **Learner model**: Bayesian Knowledge Tracing (online) plus a transformer knowledge-tracing model
  trained on GPU and served on CPU through ONNX Runtime

## Architecture

```
React (Vercel) ──Bearer token──► Flask API (HF Space, gunicorn gthread)
                                   │
                                   ├── Coordinator = LangGraph StateGraph
                                   │     START → KnowledgeAgent (learner profile)
                                   │       ├─► TeachingAgent: strategy bandit → structured lesson (LLM / cache / offline)
                                   │       ├─► AssessmentAgent: plan (target 70% success) → question bank
                                   │       │      ↺ generate_questions (one LLM call, only when the bank runs short)
                                   │       ├─► TutorAgent: hint ladder (socratic → conceptual → direct)
                                   │       └─► RecommendationAgent: readiness, ZPD, spaced-repetition urgency
                                   ├── Tutor chat = LangGraph MessagesState + SQLite checkpointer (memory per user × topic)
                                   ├── Learner model = BKT (persisted) + forgetting curve + transformer KT (ONNX)
                                   └── SQLite (WAL): users, attempts, question bank, lesson cache, bandit posteriors
```

| Agent | Decides | How |
|---|---|---|
| Knowledge | What does the learner know right now? | BKT posterior per topic, exponential forgetting, transformer KT predictions of P(correct) for every topic × difficulty |
| Teaching | How to teach this learner? | Expert rules provide the prior; a Thompson-sampling bandit learns from follow-up quiz results which strategy works per knowledge bucket |
| Assessment | Which questions, at what difficulty? | Difficulty mix chosen so predicted success ≈ 70%; unseen bank items preferred and calibrated by empirical p-correct; server-side grading |
| Tutor | How much help to give? | Hint level escalates with attempts; the LLM phrases it using the learner's code, output and mastery |
| Recommendation | What next? | Prerequisite readiness gate, learning potential, zone of proximal development, review urgency, goals |

## Knowledge-tracing results

Trained on an RTX 5090 (`training/`). Metric: test AUC for predicting the next answer.

**Real student data** (ASSISTments, standard DKVMN splits), used to validate the training harness:

| Model | ASSIST2009 | ASSIST2015 |
|---|---|---|
| BKT (per-skill, grid-search fit) | 0.711 | 0.702 |
| DKT (LSTM) | **0.819** | **0.731** |
| Transformer KT (best of a 16-config sweep) | 0.810 | 0.727 |

DKT matches published numbers. On these small datasets the transformer does not beat DKT, which is
consistent with public KT benchmarks.

**App curriculum** (20 topics, 3 difficulties, time gaps; 7.15M interactions from a learner simulator
with prerequisites, ZPD learning and forgetting):

| Model | Test AUC |
|---|---|
| Oracle (simulator's true probabilities, upper bound) | 0.719 |
| **Transformer KT, deployed (669k params, 2.7 MB ONNX)** | **0.693** |
| DKT (LSTM) | 0.689 |
| BKT | 0.654 |
| v1 heuristic tracker | 0.607 |

The deployed model captures about 88% of the achievable discrimination above chance; the v1 heuristic captured about 49%.
The simulator is not real learner data. Retrain on real logs with
`--app-db data/database.db` once the app has users; the pipeline appends them to the training set.

## Running locally

```bash
# one isolated env for the whole project (GPU wheels bundle their own CUDA runtime;
# the system driver/CUDA are untouched)
conda env create -f environment.yml && conda activate elearn

# backend (offline mode without a key: question bank + curriculum lessons)
cd backend && cp .env.example .env   # add GEMINI_API_KEY and SECRET_KEY
SESSION_COOKIE_SECURE=false python app.py          # http://localhost:7860
pytest tests -q

# frontend
cd frontend && npm install && npm run dev          # http://localhost:3000
```

Retrain the models (GPU):

```bash
python training/train_kt.py --dataset assist2009 --model all          # benchmark
python training/train_kt.py --dataset curriculum --model transformer \
  --students 100000 --d 128 --layers 3 --heads 4 --dropout 0.1 --export  # production model → backend/ml/artifacts
```

## Deployment

- **HF Space**: built from the root `Dockerfile`. Set the secrets `SECRET_KEY` and `GEMINI_API_KEY`
  (optional: `LLM_MODEL`). Enable persistent storage to keep the database across restarts; it is used
  automatically when `/data` is mounted.
- **Vercel**: root `frontend/`, env `VITE_API_URL=https://sawabedarain-adaptive-elearning-backend.hf.space`.

## API

`POST /api/register` · `POST /api/login` · `GET /api/current-user` · `PUT /api/profile`
`GET /api/topics` · `POST /api/generate-lesson` · `POST /api/generate-quiz` · `POST /api/submit-answer`
`GET /api/progress-summary` · `GET /api/knowledge-states` · `GET /api/recommendations` · `GET /api/next-topic`
`GET /api/learning-path/<id>` · `GET /api/review-queue` · `GET /api/study-tips`
`POST /api/check-code` (sandboxed subprocess) · `POST /api/ask-challenge-hint`
`POST /api/tutor/chat` · `GET|DELETE /api/tutor/history` · `GET /api/agent-status` · `GET /api/model-info` · `GET /api/health`
