from fastapi import APIRouter
from models import QueryRequest, RecommendationResponse, ExerciseRecommendation
from pipeline.query_parser import parse_query
from pipeline.retrieval import retrieve_candidates
from pipeline.reranker import rerank

router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse)
def recommend(request: QueryRequest):
    """Full recommendation pipeline: parse → retrieve → rerank."""

    # Convert Pydantic model to dict for our pipeline functions
    user_ctx = {}
    if request.user_context:
        user_ctx = request.user_context.model_dump()

    # Step 1: Parse query
    parsed = parse_query(request.query, user_ctx if user_ctx else None)
    print(f"Parsed: {parsed}")

    # Step 2: Retrieve candidates
    from main import app
    candidates = retrieve_candidates(parsed, app.state.db_conn, app.state.embeddings)
    print(f"Retrieved {len(candidates)} candidates")

    # Step 3: Rerank with LLM
    ranked = rerank(request.query, user_ctx, candidates)
    print(f"LLM returned {len(ranked)} ranked results")

    # Merge LLM rankings with full exercise data
    exercise_map = {c["id"]: c for c in candidates}
    recommendations = []
    for item in ranked:
        ex = exercise_map.get(item["id"])
        if ex:
            recommendations.append(ExerciseRecommendation(
                rank=item["rank"],
                id=ex["id"],
                title=ex["title"],
                description=ex["description"],
                body_part=ex["body_part"],
                difficulty=ex["difficulty"],
                equipment=ex["equipment"],
                injury_focus=ex["injury_focus"],
                intensity=ex["intensity"],
                reason=item["reason"]
            ))

    return RecommendationResponse(
        recommendations=recommendations,
        query_interpretation=f"Filters: {parsed.filters}, Semantic: '{parsed.semantic_query}'",
        candidates_evaluated=len(candidates)
    )