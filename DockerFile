FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy everything needed
COPY exercises.csv .
COPY backend/ ./

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}