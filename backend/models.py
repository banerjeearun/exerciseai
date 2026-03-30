from pydantic import BaseModel


class UserContext(BaseModel):
    goal: str | None = None
    injuries: list[str] = []
    equipment: list[str] = []
    intensity_preference: str | None = None


class QueryRequest(BaseModel):
    query: str
    user_context: UserContext | None = None


class ExerciseRecommendation(BaseModel):
    rank: int
    id: str
    title: str
    description: str
    body_part: str
    difficulty: str
    equipment: str
    injury_focus: str
    intensity: str
    reason: str


class RecommendationResponse(BaseModel):
    recommendations: list[ExerciseRecommendation]
    query_interpretation: str
    candidates_evaluated: int