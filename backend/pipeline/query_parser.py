class ParsedQuery:
    def __init__(self, filters, exclude_equipment, semantic_query):
        self.filters = filters
        self.exclude_equipment = exclude_equipment
        self.semantic_query = semantic_query

    def __repr__(self):
        return (f"ParsedQuery(filters={self.filters}, "
                f"exclude={self.exclude_equipment}, "
                f"query='{self.semantic_query}')")


# Synonym maps — each key is a canonical value, each list contains
# words/phrases that should map to it
BODY_PART_SYNONYMS = {
    "upper": [
        "upper body", "arm", "arms", "shoulder", "shoulders", "chest",
        "push", "press", "pull", "back", "bicep", "tricep", "lat",
        "pec", "upper half", "above the waist"
    ],
    "lower": [
        "lower body", "leg", "legs", "knee", "knees", "hip", "hips",
        "glute", "glutes", "squat", "lunge", "calf", "calves", "ankle",
        "ankles", "quad", "quads", "hamstring", "hamstrings", "thigh",
        "lower half", "below the waist"
    ],
    "core": [
        "core", "abs", "abdominal", "plank", "spine", "torso",
        "midsection", "oblique", "obliques"
    ],
    "full body": [
        "full body", "total body", "conditioning", "cardio",
        "whole body", "entire body", "everything"
    ],
}

INTENSITY_SYNONYMS = {
    "low": [
        "low impact", "low intensity", "gentle", "easy", "light",
        "beginner friendly", "recovery", "rehab", "mobility",
        "no impact", "safe"
    ],
    "high": [
        "high intensity", "explosive", "intense", "hard", "heavy",
        "advanced", "power", "plyometric", "max effort", "sprint"
    ],
    "medium": [
        "medium intensity", "moderate", "medium"
    ],
}

INJURY_SYNONYMS = {
    "knee": ["knee", "knees", "acl", "mcl", "meniscus", "patella", "kneecap"],
    "shoulder": ["shoulder", "shoulders", "rotator cuff", "deltoid"],
    "hip": ["hip", "hips", "groin", "adductor"],
    "back": ["back", "lower back", "spine", "spinal", "lumbar", "disc"],
    "ankle": ["ankle", "ankles", "achilles", "foot"],
    "hamstring": ["hamstring", "hamstrings", "ham"],
}

# Words that signal the user wants to AVOID something
EXCLUSION_SIGNALS = {
    "no weights": ["barbell", "dumbbell", "kettlebell", "cable", "machine"],
    "no equipment": ["barbell", "dumbbell", "kettlebell", "cable", "machine", "band", "bar", "sled", "rope", "ladder", "bike"],
    "bodyweight only": ["barbell", "dumbbell", "kettlebell", "cable", "machine", "sled"],
    "no machines": ["machine", "cable"],
    "no barbell": ["barbell"],
    "no dumbbells": ["dumbbell"],
}


def _find_match(query_lower, synonym_map):
    """Check if any synonym from the map appears in the query.
    Returns the canonical key if found, None otherwise.
    Checks longer phrases first to avoid partial matches.
    """
    for canonical, synonyms in synonym_map.items():
        # Sort by length descending — match "lower body" before "lower"
        for phrase in sorted(synonyms, key=len, reverse=True):
            if phrase in query_lower:
                return canonical
    return None


def _find_all_matches(query_lower, synonym_map):
    """Like _find_match but returns ALL matching canonical keys."""
    matches = []
    for canonical, synonyms in synonym_map.items():
        for phrase in synonyms:
            if phrase in query_lower:
                matches.append(canonical)
                break  # found one synonym for this key, move to next
    return matches


def parse_query(query, user_context=None):
    """Extract structured filters from query text and user context.
    
    Uses synonym matching (not exact keywords) to handle natural phrasing.
    The onboarding form (user_context) provides the most reliable filters.
    Query text parsing is a best-effort supplement.
    """
    filters = {}
    exclude_equipment = set()
    query_lower = query.lower()

    # === From onboarding form (most reliable) ===
    if user_context:
        if user_context.get("injuries"):
            filters["injury_focus"] = [
                f"{inj} rehab" for inj in user_context["injuries"]
            ]

        if user_context.get("equipment"):
            all_equipment = {
                "bodyweight", "none", "band", "barbell", "dumbbell",
                "cable", "bar", "kettlebell", "sled", "machine", "bike",
                "rope", "ladder"
            }
            user_has = set(user_context["equipment"])
            exclude_equipment = all_equipment - user_has - {"none"}

        if user_context.get("intensity_preference"):
            filters["intensity"] = user_context["intensity_preference"]

    # === From query text (best-effort) ===

    # Detect body part
    body_part = _find_match(query_lower, BODY_PART_SYNONYMS)
    if body_part:
        filters["body_part"] = body_part

    # Detect intensity (only if not already set by onboarding)
    if "intensity" not in filters:
        intensity = _find_match(query_lower, INTENSITY_SYNONYMS)
        if intensity:
            filters["intensity"] = intensity

    # Detect injuries from query text (supplement onboarding)
    detected_injuries = _find_all_matches(query_lower, INJURY_SYNONYMS)
    if detected_injuries:
        existing = filters.get("injury_focus", [])
        for inj in detected_injuries:
            rehab_val = f"{inj} rehab"
            if rehab_val not in existing:
                existing.append(rehab_val)
        if existing:
            filters["injury_focus"] = existing

    # Detect equipment exclusions from query text
    for phrase, excluded in EXCLUSION_SIGNALS.items():
        if phrase in query_lower:
            exclude_equipment.update(excluded)

    return ParsedQuery(
        filters=filters,
        exclude_equipment=list(exclude_equipment),
        semantic_query=query
    )


if __name__ == "__main__":
    tests = [
        ("my shoulders hurt and I need gentle exercises", None),
        ("I don't have any equipment, just bodyweight only", None),
        ("explosive drills for a winger", None),
        ("my knees are bad, need low impact rehab", None),
        ("upper body rehab no weights",
         {"equipment": ["bodyweight", "band"], "injuries": ["shoulder"]}),
        ("help me with my acl recovery", None),
        ("quad and hamstring work, no machines", None),
    ]

    for query, ctx in tests:
        parsed = parse_query(query, ctx)
        print(f"\nQuery: '{query}'")
        if ctx:
            print(f"  Context: {ctx}")
        print(f"  {parsed}")