import psycopg2
from pipeline.embeddings import EmbeddingsStore

# Load exercises from database
conn = psycopg2.connect(
    host="localhost", port=5432, dbname="coaching",
    user="postgres", password="postgres"
)
cur = conn.cursor()
cur.execute("SELECT id, title, description, tags, body_part, injury_focus FROM exercises")
columns = [desc[0] for desc in cur.description]
exercises = [dict(zip(columns, row)) for row in cur.fetchall()]
cur.close()
conn.close()

# Build embeddings
store = EmbeddingsStore()
store.precompute(exercises)

# Test queries
test_queries = [
    "knee pain low impact",
    "explosive drills for a winger",
    "upper body rehab no weights",
]

for query in test_queries:
    print(f"\n--- Query: '{query}' ---")
    query_vec = store.encode(query)
    
    # Score every exercise
    scores = []
    for ex in exercises:
        score = store.similarity(query_vec, ex["id"])
        scores.append((ex["id"], ex["title"], score))
    
    # Sort by score descending, show top 5
    scores.sort(key=lambda x: x[2], reverse=True)
    for rank, (ex_id, title, score) in enumerate(scores[:5], 1):
        print(f"  {rank}. {title} (score: {score:.3f})")