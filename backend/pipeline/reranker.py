import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()

RERANK_PROMPT = """You are a sports science and rehabilitation expert.

A user is looking for exercise recommendations. Given their query, their profile, 
and a list of candidate exercises, select and rank the TOP 5 most relevant exercises.

Consider these criteria in order of importance:
1. SAFETY — Does the exercise avoid aggravating the user's injuries?
2. GOAL ALIGNMENT — Does it serve their stated goal (rehab, strength, etc.)?
3. EQUIPMENT MATCH — Can they perform it with their available equipment?
4. DIFFICULTY FIT — Is it appropriate for their level?
5. SPECIFICITY — How directly does it address what they asked for?

User query: "{query}"

User profile:
- Goal: {goal}
- Injuries/concerns: {injuries}
- Available equipment: {equipment}
- Intensity preference: {intensity}

Candidate exercises:
{candidates}

Return ONLY a valid JSON array of exactly 5 exercises, ranked best first.
No markdown, no explanation outside the JSON. Format:
[
  {{"id": "EX_001", "rank": 1, "reason": "One sentence why this is the best fit"}},
  {{"id": "EX_002", "rank": 2, "reason": "One sentence why this is second"}},
  {{"id": "EX_003", "rank": 3, "reason": "One sentence explanation"}},
  {{"id": "EX_004", "rank": 4, "reason": "One sentence explanation"}},
  {{"id": "EX_005", "rank": 5, "reason": "One sentence explanation"}}
]"""


def format_candidates(candidates):
    """Format candidate exercises into a readable string for the LLM."""
    lines = []
    for ex in candidates:
        tags = ex["tags"] if isinstance(ex["tags"], str) else ", ".join(ex["tags"])
        lines.append(
            f"- {ex['id']}: {ex['title']} | {ex['description']} | "
            f"body: {ex['body_part']} | difficulty: {ex['difficulty']} | "
            f"equipment: {ex['equipment']} | injury_focus: {ex['injury_focus']} | "
            f"intensity: {ex['intensity']} | tags: {tags}"
        )
    return "\n".join(lines)


def rerank(query, user_context, candidates):
    """Send candidates to Claude Sonnet for intelligent re-ranking.
    
    The LLM sees the full picture: user's query, their profile (injuries,
    equipment, goals), and all candidate metadata. It reasons about things
    embeddings can't — like whether a 'beginner' exercise is appropriate
    for someone rehabbing an ACL, or whether 'explosive' exercises are 
    safe for someone with knee pain.
    """
    # Build the prompt
    prompt = RERANK_PROMPT.format(
        query=query,
        goal=user_context.get("goal", "not specified"),
        injuries=", ".join(user_context.get("injuries", [])) or "none reported",
        equipment=", ".join(user_context.get("equipment", [])) or "any",
        intensity=user_context.get("intensity_preference", "any"),
        candidates=format_candidates(candidates)
    )

    # Call Claude Sonnet
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse the JSON response
    text = response.content[0].text.strip()
    # Strip markdown code fences if the model adds them
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        ranked = json.loads(text)
        return ranked
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response as JSON: {text[:200]}")
        # Fallback: return first 5 candidates in retrieval order
        return [
            {"id": c["id"], "rank": i + 1, "reason": "Ranked by retrieval score"}
            for i, c in enumerate(candidates[:5])
        ]