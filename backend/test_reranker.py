import psycopg2
from pipeline.embeddings import EmbeddingsStore
from pipeline.query_parser import parse_query
from pipeline.retrieval import retrieve_candidates
from pipeline.reranker import rerank

# Setup
conn = psycopg2.connect(
    host="localhost", port=5432, dbname="coaching",
    user="postgres", password="postgres"
)
cur = conn.cursor()
cur.execute("SELECT id, title, description, tags, body_part, injury_focus FROM exercises")
columns = [desc[0] for desc in cur.description]
exercises = [dict(zip(columns, row)) for row in cur.fetchall()]
cur.close()

store = EmbeddingsStore()
store.precompute(exercises)

# Test the full pipeline: parse → retrieve → rerank
query = "upper body rehab no weights"
user_context = {
    "goal": "rehab",
    "injuries": ["shoulder"],
    "equipment": ["bodyweight", "band"],
    "intensity_preference": "low"
}

print(f"Query: '{query}'")
print(f"Context: {user_context}\n")

# Step 1: Parse
parsed = parse_query(query, user_context)
print(f"Parsed: {parsed}\n")

# Step 2: Retrieve
candidates = retrieve_candidates(parsed, conn, store)
print(f"\nRetrieval returned {len(candidates)} candidates")
print("--- Retrieval order (before LLM) ---")
for i, c in enumerate(candidates, 1):
    print(f"  {i}. {c['title']} | {c['body_part']} | {c['equipment']} | score: {c['similarity_score']}")

# Step 3: Rerank with LLM
print("\n--- Calling Claude Sonnet for re-ranking... ---\n")
ranked = rerank(query, user_context, candidates)

print("--- Final recommendations (after LLM) ---")
for r in ranked:
    print(f"  #{r['rank']}: {r['id']} — {r['reason']}")

conn.close()
