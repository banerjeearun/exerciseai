import os
import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pipeline.embeddings import EmbeddingsStore


def get_db_connection():
    """Connect using Railway's DATABASE_URL or local defaults."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Railway provides a full connection string
        return psycopg2.connect(database_url)
    else:
        # Local development
        return psycopg2.connect(
            host="localhost", port=5432, dbname="coaching",
            user="postgres", password="postgres"
        )


def ensure_schema(conn):
    """Create the exercises table if it doesn't exist."""
    cur = conn.cursor()
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS exercises (
            id            VARCHAR(10) PRIMARY KEY,
            title         VARCHAR(255) NOT NULL,
            description   TEXT,
            tags          TEXT[],
            body_part     VARCHAR(50),
            difficulty    VARCHAR(20),
            equipment     VARCHAR(50),
            injury_focus  VARCHAR(50),
            intensity     VARCHAR(20)
        );
    """)
    conn.commit()
    cur.close()


def seed_if_empty(conn):
    """Auto-seed the database if the exercises table is empty."""
    import csv

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM exercises")
    count = cur.fetchone()[0]

    if count > 0:
        print(f"Database already has {count} exercises — skipping seed")
        cur.close()
        return

    print("Database empty — seeding exercises...")

    # Try multiple possible paths for the CSV
    csv_path = None
    for path in ["exercises.csv", "../exercises.csv", "/app/exercises.csv"]:
        if os.path.exists(path):
            csv_path = path
            break

    if not csv_path:
        print("WARNING: exercises.csv not found — cannot seed")
        cur.close()
        return

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        inserted = 0
        for row in reader:
            # Fix the 'full body' CSV bug
            if row["body_part"] == "full" and row["difficulty"] == "body":
                row["body_part"] = "full body"
                row["difficulty"] = row["equipment"]
                row["equipment"] = row["injury_focus"]
                row["injury_focus"] = row["intensity"]
                row["intensity"] = row.get("", "").strip()

            tags = [t.strip() for t in row["tags"].split(",") if t.strip()]

            cur.execute(
                """
                INSERT INTO exercises (id, title, description, tags, body_part,
                                       difficulty, equipment, injury_focus, intensity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (row["id"], row["title"], row["description"], tags,
                 row["body_part"], row["difficulty"], row["equipment"],
                 row["injury_focus"], row["intensity"])
            )
            inserted += 1

    conn.commit()
    cur.close()
    print(f"Seeded {inserted} exercises")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect DB, ensure schema, seed data, load embeddings."""
    print("Starting ExerciseAI...")

    # Database
    app.state.db_conn = get_db_connection()
    print("Connected to database")

    ensure_schema(app.state.db_conn)
    seed_if_empty(app.state.db_conn)

    # Embeddings
    cur = app.state.db_conn.cursor()
    cur.execute("SELECT id, title, description, tags, body_part, injury_focus FROM exercises")
    columns = [desc[0] for desc in cur.description]
    exercises = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()

    app.state.embeddings = EmbeddingsStore()
    app.state.embeddings.precompute(exercises)
    print(f"Ready — {len(exercises)} exercises loaded")

    yield

    app.state.db_conn.close()
    print("Shutdown complete")


app = FastAPI(
    title="ExerciseAI",
    description="AI-powered exercise recommendation engine",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
from api.routes import router
app.include_router(router)

# Serve React frontend (must be after API routes)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")