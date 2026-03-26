def retrieve_candidates(parsed_query, db_conn, embeddings_store, top_k=10):
    """Retrieve exercises using SQL filters + embedding ranking.
    
    Progressive filter relaxation:
    1. Try all filters (body_part + intensity + equipment exclusion)
    2. If < 5 results, drop intensity
    3. If still < 5, drop body_part too
    This ensures we always return enough candidates for the re-ranker.
    """
    cur = db_conn.cursor()
    columns = "id, title, description, tags, body_part, difficulty, equipment, injury_focus, intensity"

    def build_query(use_body_part=True, use_intensity=True):
        conditions = []
        params = []

        if use_body_part and "body_part" in parsed_query.filters:
            conditions.append("body_part = %s")
            params.append(parsed_query.filters["body_part"])

        if use_intensity and "intensity" in parsed_query.filters:
            conditions.append("intensity = %s")
            params.append(parsed_query.filters["intensity"])

        if parsed_query.exclude_equipment:
            placeholders = ",".join(["%s"] * len(parsed_query.exclude_equipment))
            conditions.append(f"equipment NOT IN ({placeholders})")
            params.extend(parsed_query.exclude_equipment)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        return f"SELECT {columns} FROM exercises {where}", params

    def execute_query(sql, params):
        cur.execute(sql, params)
        col_names = [desc[0] for desc in cur.description]
        return [dict(zip(col_names, row)) for row in cur.fetchall()]

    # Try with all filters
    sql, params = build_query(use_body_part=True, use_intensity=True)
    rows = execute_query(sql, params)
    print(f"  Filters: {parsed_query.filters}")
    print(f"  Equipment excluded: {len(parsed_query.exclude_equipment)} types")
    print(f"  Candidates (all filters): {len(rows)}")

    # Relax intensity first (body_part matters more)
    if len(rows) < 5 and "intensity" in parsed_query.filters:
        sql, params = build_query(use_body_part=True, use_intensity=False)
        rows = execute_query(sql, params)
        print(f"  Relaxed intensity → {len(rows)} candidates")

    # Relax body_part too if still too few
    if len(rows) < 5 and "body_part" in parsed_query.filters:
        sql, params = build_query(use_body_part=False, use_intensity=False)
        rows = execute_query(sql, params)
        print(f"  Relaxed body_part → {len(rows)} candidates")

    cur.close()

    # Rank by embedding similarity
    query_vec = embeddings_store.encode(parsed_query.semantic_query)
    for row in rows:
        row["similarity_score"] = round(
            embeddings_store.similarity(query_vec, row["id"]), 4
        )

    rows.sort(key=lambda x: x["similarity_score"], reverse=True)
    return rows[:top_k]