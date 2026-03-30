import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pipeline.embeddings import EmbeddingsStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to DB, load embeddings. Shutdown: close connection."""

    # Connect to Postgres
    print("Connecting to database...")
    app.state.db_conn = psycopg2.connect(
        host="localhost", port=5432, dbname="coaching",
        user="postgres", password="postgres"
    )
    print("Connected")

    # Load exercises and pre-compute embeddings
    print("Loading embeddings...")
    cur = app.state.db_conn.cursor()
    cur.execute("SELECT id, title, description, tags, body_part, injury_focus FROM exercises")
    columns = [desc[0] for desc in cur.description]
    exercises = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()

    app.state.embeddings = EmbeddingsStore()
    app.state.embeddings.precompute(exercises)
    print(f"Ready — {len(exercises)} exercises loaded")

    yield

    # Shutdown
    app.state.db_conn.close()
    print("Database connection closed")


app = FastAPI(
    title="ExerciseAI",
    description="AI-powered exercise recommendation engine",
    lifespan=lifespan
)

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from api.routes import router
app.include_router(router)