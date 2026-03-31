# ExerciseAI

AI-powered exercise recommendation engine that takes natural language queries and returns personalized exercise recommendations using retrieval + LLM re-ranking.

**Live Demo**: https://exerciseai-production.up.railway.app

## Architecture

```
User query + profile → Query Parser (Python) → Filtered Retrieval (SQL + Embeddings) → LLM Re-ranker (Claude Sonnet) → Top 5 recommendations
```

The system uses a two-stage retrieval-then-rerank architecture:

1. **Query Parser** — Pure Python. Extracts structured filters (body part, intensity, equipment exclusions) from the user's onboarding profile and query text using synonym matching. No LLM needed for this step.

2. **Retrieval** — Combines SQL WHERE clause filtering (from parsed filters) with semantic embedding similarity (all-MiniLM-L6-v2, 384 dims). Filters narrow 60 exercises to ~10-20 candidates, embeddings rank them. Progressive filter relaxation ensures enough candidates are returned even when filters are strict.

3. **LLM Re-ranking** — Single Claude Sonnet API call. Receives the user's query, profile context, and 10 candidate exercises. Returns top 5 ranked by safety, goal alignment, equipment fit, and difficulty appropriateness — with a one-sentence explanation for each.

### Why two stages?

Retrieval is fast (~50ms) and cheap but cannot reason about injury safety or exercise progression. The LLM is slow (~1.5s) and costs ~$0.007 per request but provides expert-level reasoning. By combining them, we get speed from retrieval and intelligence from the LLM. The LLM never sees more than 10 candidates regardless of dataset size, making this architecture scalable.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2), in-memory at 60 exercises
- **LLM**: Claude Sonnet via Anthropic API
- **Frontend**: React (minimal, single page)
- **Deployment**: Railway (single service serving both API and static frontend)

## Data Setup

### CSV Data Quality Fix

The provided `exercises.csv` has a parsing bug in 10 out of 60 rows. Rows where `body_part` should be "full body" have the value split across two columns because "full body" is unquoted. This shifts all subsequent fields one position right.

**Detection**: `body_part == "full"` AND `difficulty == "body"`

The seed script detects and fixes this automatically during ingestion. Affected rows: EX_015, EX_016, EX_018, EX_044, EX_048, EX_049, EX_050, EX_058, EX_059, EX_060.

### Schema Modifications

1. `tags` converted from comma-separated string to PostgreSQL `TEXT[]` array for proper querying
2. Added auto-seeding on startup — the app seeds the database if the exercises table is empty
3. Fixed "full body" column shift bug during ingestion

## Local Development

### Prerequisites

- Docker (for PostgreSQL)
- Python 3.11+
- Node.js 18+ (for frontend development)
- Anthropic API key

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/exerciseai.git
cd exerciseai

# Start PostgreSQL
docker compose up -d

# Create Python environment
conda create -n exerciseai python=3.11
conda activate exerciseai
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Seed the database
python backend/db/seed.py

# Start the backend
cd backend
uvicorn main:app --reload --port 8000

# In another terminal — frontend development (optional)
cd frontend
npm install
npm start
```

The app is available at http://localhost:8000 (API + frontend) or http://localhost:3000 (React dev server).

## API

### POST /recommend

```json
{
  "query": "knee pain low impact exercises",
  "user_context": {
    "goal": "rehab",
    "injuries": ["knee"],
    "equipment": ["bodyweight", "band"],
    "intensity_preference": "low"
  }
}
```

Returns ranked exercises with LLM-generated reasoning. Interactive API docs at `/docs`.

## Scaling Discussion

### 100k+ exercises

- Move embeddings from in-memory numpy to pgvector with HNSW index for sub-millisecond ANN search
- SQL WHERE pre-filtering before vector search reduces candidate pool by ~80%
- Add query result caching (LRU keyed on normalized query + user context hash)
- The LLM re-ranker never sees more than 10-15 candidates regardless of dataset size — this is the key constraint that keeps costs constant

### Concurrent users

- FastAPI is async-native, handles concurrent requests out of the box
- asyncpg connection pool (min=5, max=20) would replace the current synchronous connection
- Rate-limit Claude API calls with a concurrency limiter (~10 concurrent)
- Cache frequent query patterns to avoid redundant LLM calls
- Embedding model is CPU-bound — at scale, move to a separate inference service or use an embedding API

### Production improvements

- Add LLM-powered query understanding (Haiku) before retrieval for highly ambiguous queries
- Cross-encoder re-ranking as an intermediate step between embedding retrieval and LLM re-ranking
- Feedback loop: track which recommendations users complete to improve future rankings
- A/B test retrieval strategies (pure embedding vs hybrid keyword + embedding)

## Personalization Proposal

### What to collect at onboarding

Goals (strength, rehab, endurance, sport-specific performance), injury history and current constraints, available equipment, preferred intensity and session duration, sport and position (for sport-specific recommendations), and training experience level.

### How it influences the pipeline

**Retrieval**: Hard filters (exclude unavailable equipment, cap difficulty for beginners) and soft boosts (weight rehab exercises higher for users with injury history). The current implementation demonstrates this with the onboarding form → SQL WHERE clause path.

**Re-ranking**: User context is injected directly into the LLM prompt. The LLM reasons about exercise safety and progression with full user context — for example, avoiding explosive plyometrics for a user with knee pain even if those exercises score high on embedding similarity.

**Over time**: The initial onboarding form bootstraps the preference model (like Spotify's genre selection at signup). As users interact — completing exercises, rating them, skipping recommendations — implicit behavioral signals build a richer profile. This enables collaborative filtering: "users with similar injury profiles who completed exercise X also benefited from exercise Y."

### Inspiration from Spotify / Netflix

- Spotify's Discover Weekly succeeds by combining collaborative filtering (users like you) with content-based filtering (acoustic similarity). Our analogue: users with similar injury/goal profiles + exercise metadata similarity.
- Netflix's onboarding (pick 3 shows you like) solves the cold-start problem. Our onboarding form serves the same purpose — enough signal to make useful recommendations from request #1.
- Both systems transition from explicit preferences (onboarding) to implicit signals (behavior) over time. The production version of this system would follow the same trajectory.
