import csv
import psycopg2

# Connect to Postgres
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="coaching",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()
print("Connected to database")

# Clear existing data
cur.execute("DELETE FROM exercises")
print("Cleared old data")

# Read CSV
count = 0
with open("exercises.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Fix the 'full body' bug
        if row["body_part"] == "full" and row["difficulty"] == "body":
            row["body_part"] = "full body"
            row["difficulty"] = row["equipment"]
            row["equipment"] = row["injury_focus"]
            row["injury_focus"] = row["intensity"]
            row["intensity"] = row.get("", "").strip()

        # Parse tags from comma string to list
        tags = [t.strip() for t in row["tags"].split(",") if t.strip()]

        cur.execute(
            """
            INSERT INTO exercises (id, title, description, tags, body_part,
                                   difficulty, equipment, injury_focus, intensity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row["id"],
                row["title"],
                row["description"],
                tags,
                row["body_part"],
                row["difficulty"],
                row["equipment"],
                row["injury_focus"],
                row["intensity"],
            )
        )
        count += 1
        if count % 10 == 0:
            print(f"  Inserted {count} rows...")

conn.commit()
print(f"\nDone! Seeded {count} exercises")

# Verify
cur.execute("SELECT COUNT(*) FROM exercises")
print(f"Total in database: {cur.fetchone()[0]}")

cur.execute("SELECT DISTINCT body_part FROM exercises ORDER BY body_part")
print(f"Body parts: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT DISTINCT difficulty FROM exercises ORDER BY difficulty")
print(f"Difficulties: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT COUNT(*) FROM exercises WHERE body_part = 'full body'")
print(f"Fixed 'full body' rows: {cur.fetchone()[0]}")

cur.close()
conn.close()