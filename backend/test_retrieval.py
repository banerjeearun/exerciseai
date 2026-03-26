import psycopg2
from pipeline.embeddings import EmbeddingsStore
from pipeline.query_parser import parse_query
from pipeline.retrieval import retrieve_candidates

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

# Test 1: Knee pain with no context
print("\n========== TEST 1: 'knee pain low impact' ==========")
parsed = parse_query("knee pain low impact")
print(f"Parsed: {parsed}")
results = retrieve_candidates(parsed, conn, store)
for i, r in enumerate(results, 1):
    print(f"  {i}. {r['title']} | {r['body_part']} | {r['difficulty']} | "
          f"{r['equipment']} | {r['injury_focus']} | score: {r['similarity_score']}")

# Test 2: Upper body rehab with onboarding context
print("\n========== TEST 2: 'upper body rehab no weights' ==========")
parsed = parse_query(
    "upper body rehab no weights",
    user_context={"equipment": ["bodyweight", "band"], "injuries": ["shoulder"]}
)
print(f"Parsed: {parsed}")
results = retrieve_candidates(parsed, conn, store)
for i, r in enumerate(results, 1):
    print(f"  {i}. {r['title']} | {r['body_part']} | {r['difficulty']} | "
          f"{r['equipment']} | {r['injury_focus']} | score: {r['similarity_score']}")

# Test 3: Sport-specific query
print("\n========== TEST 3: 'explosive drills for a winger' ==========")
parsed = parse_query("explosive drills for a winger")
print(f"Parsed: {parsed}")
results = retrieve_candidates(parsed, conn, store)
for i, r in enumerate(results, 1):
    print(f"  {i}. {r['title']} | {r['body_part']} | {r['difficulty']} | "
          f"{r['equipment']} | {r['injury_focus']} | score: {r['similarity_score']}")

conn.close()