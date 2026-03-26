from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingsStore:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = {}  # exercise_id -> numpy vector
        print("Model loaded")

    def build_text(self, exercise):
        """Combine exercise fields into a single string for embedding.
        
        We include the fields that carry the most semantic meaning.
        Title and description are the richest. Tags add specificity.
        body_part and injury_focus help the model understand the category.
        """
        parts = [
            exercise["title"],
            exercise["description"],
            exercise["tags"] if isinstance(exercise["tags"], str) 
                else " ".join(exercise["tags"]),
            exercise["body_part"],
            exercise["injury_focus"] if exercise["injury_focus"] != "none" else ""
        ]
        return " | ".join(p for p in parts if p)

    def encode(self, text):
        """Encode a single text string into a normalized vector."""
        return self.model.encode(text, normalize_embeddings=True)

    def precompute(self, exercises):
        """Encode all exercises at once (batch encoding is much faster)."""
        texts = [self.build_text(ex) for ex in exercises]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        for ex, vec in zip(exercises, vectors):
            self.embeddings[ex["id"]] = vec
        print(f"Pre-computed embeddings for {len(exercises)} exercises")

    def similarity(self, query_vec, exercise_id):
        """Cosine similarity between a query vector and a stored exercise.
        
        Because both vectors are normalized (length = 1), 
        cosine similarity = dot product. That's why we set
        normalize_embeddings=True above.
        """
        ex_vec = self.embeddings.get(exercise_id)
        if ex_vec is None:
            return 0.0
        return float(np.dot(query_vec, ex_vec))