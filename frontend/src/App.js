import { useState } from "react";

const API_URL = "http://localhost:8000";

// ============ Onboarding Form ============
function OnboardingForm({ context, setContext }) {
  const goals = ["rehab", "strength", "endurance", "performance"];
  const injuryOptions = ["knee", "shoulder", "hip", "back", "ankle"];
  const equipmentOptions = [
    "band", "dumbbell", "barbell", 
    "kettlebell", "cable", "machine", "bar"
  ];
  const intensities = ["low", "medium", "high"];

  const toggleItem = (field, item) => {
    const current = context[field] || [];
    if (current.includes(item)) {
      setContext({ ...context, [field]: current.filter((i) => i !== item) });
    } else {
      setContext({ ...context, [field]: [...current, item] });
    }
  };

  return (
    <div style={{ 
      background: "#f8f9fa", borderRadius: 12, padding: 24, 
      marginBottom: 24 
    }}>
      <h3 style={{ margin: "0 0 16px", fontSize: 16 }}>Your Profile</h3>

      {/* Goal */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 13, color: "#666", display: "block", marginBottom: 6 }}>
          Goal
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {goals.map((g) => (
            <button
              key={g}
              onClick={() => setContext({ ...context, goal: context.goal === g ? null : g })}
              style={{
                padding: "6px 14px", borderRadius: 20, border: "1px solid #ddd",
                background: context.goal === g ? "#2563eb" : "white",
                color: context.goal === g ? "white" : "#333",
                cursor: "pointer", fontSize: 13,
              }}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* Injuries */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 13, color: "#666", display: "block", marginBottom: 6 }}>
          Injuries / Concerns
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {injuryOptions.map((inj) => (
            <button
              key={inj}
              onClick={() => toggleItem("injuries", inj)}
              style={{
                padding: "6px 14px", borderRadius: 20, border: "1px solid #ddd",
                background: (context.injuries || []).includes(inj) ? "#dc2626" : "white",
                color: (context.injuries || []).includes(inj) ? "white" : "#333",
                cursor: "pointer", fontSize: 13,
              }}
            >
              {inj}
            </button>
          ))}
        </div>
      </div>

      {/* Equipment */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 13, color: "#666", display: "block", marginBottom: 6 }}>
          Available Equipment
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {equipmentOptions.map((eq) => (
            <button
              key={eq}
              onClick={() => toggleItem("equipment", eq)}
              style={{
                padding: "6px 14px", borderRadius: 20, border: "1px solid #ddd",
                background: (context.equipment || []).includes(eq) ? "#16a34a" : "white",
                color: (context.equipment || []).includes(eq) ? "white" : "#333",
                cursor: "pointer", fontSize: 13,
              }}
            >
              {eq}
            </button>
          ))}
        </div>
      </div>

      {/* Intensity */}
      <div>
        <label style={{ fontSize: 13, color: "#666", display: "block", marginBottom: 6 }}>
          Intensity Preference
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          {intensities.map((level) => (
            <button
              key={level}
              onClick={() => setContext({ ...context, intensity_preference: context.intensity_preference === level ? null : level })}
              style={{
                padding: "6px 14px", borderRadius: 20, border: "1px solid #ddd",
                background: context.intensity_preference === level ? "#9333ea" : "white",
                color: context.intensity_preference === level ? "white" : "#333",
                cursor: "pointer", fontSize: 13,
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ Search Bar ============
function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 12, marginBottom: 24 }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Describe what you need... e.g. 'knee pain low impact exercises'"
        style={{
          flex: 1, padding: "12px 16px", borderRadius: 8,
          border: "1px solid #ddd", fontSize: 15,
        }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: "12px 24px", borderRadius: 8, border: "none",
          background: loading ? "#93c5fd" : "#2563eb", color: "white",
          fontSize: 15, cursor: loading ? "wait" : "pointer",
          whiteSpace: "nowrap",
        }}
      >
        {loading ? "Thinking..." : "Get Recommendations"}
      </button>
    </form>
  );
}

// ============ Result Card ============
function ResultCard({ exercise }) {
  const difficultyColor = {
    beginner: "#16a34a",
    intermediate: "#ca8a04",
    advanced: "#dc2626",
  };

  return (
    <div style={{
      background: "white", borderRadius: 12, padding: 20,
      border: "1px solid #e5e7eb", marginBottom: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <span style={{
              background: "#2563eb", color: "white", width: 28, height: 28,
              borderRadius: "50%", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 13, fontWeight: 600,
            }}>
              {exercise.rank}
            </span>
            <h3 style={{ margin: 0, fontSize: 17 }}>{exercise.title}</h3>
          </div>
          <p style={{ margin: "0 0 12px", color: "#666", fontSize: 14 }}>
            {exercise.description}
          </p>
        </div>
      </div>

      {/* Tags */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span style={{
          padding: "3px 10px", borderRadius: 12, fontSize: 12,
          background: "#eff6ff", color: "#2563eb",
        }}>
          {exercise.body_part}
        </span>
        <span style={{
          padding: "3px 10px", borderRadius: 12, fontSize: 12,
          background: "#f0fdf4",
          color: difficultyColor[exercise.difficulty] || "#333",
        }}>
          {exercise.difficulty}
        </span>
        <span style={{
          padding: "3px 10px", borderRadius: 12, fontSize: 12,
          background: "#faf5ff", color: "#9333ea",
        }}>
          {exercise.equipment}
        </span>
        <span style={{
          padding: "3px 10px", borderRadius: 12, fontSize: 12,
          background: "#fff7ed", color: "#c2410c",
        }}>
          {exercise.intensity} intensity
        </span>
      </div>

      {/* LLM Reasoning */}
      <div style={{
        background: "#f8f9fa", borderRadius: 8, padding: 12,
        fontSize: 14, color: "#444", lineHeight: 1.5,
        borderLeft: "3px solid #2563eb",
      }}>
        {exercise.reason}
      </div>
    </div>
  );
}

// ============ Main App ============
function App() {
  const [context, setContext] = useState({
    goal: null,
    injuries: [],
    equipment: [],
    intensity_preference: null,
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          user_context: {
             ...context,
            equipment: ["bodyweight", "none", ...(context.equipment || [])],
        },
   }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "40px 20px" }}>
      <h1 style={{ fontSize: 28, marginBottom: 4 }}>ExerciseAI</h1>
      <p style={{ color: "#666", marginBottom: 32, fontSize: 15 }}>
        AI-powered exercise recommendations tailored to your needs
      </p>

      <OnboardingForm context={context} setContext={setContext} />
      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <div style={{
          background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
          padding: 16, color: "#dc2626", marginBottom: 16, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {results && (
        <div>
          <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>
            Evaluated {results.candidates_evaluated} exercises — showing top {results.recommendations.length}
          </p>
          {results.recommendations.map((ex) => (
            <ResultCard key={ex.id} exercise={ex} />
          ))}
        </div>
      )}
    </div>
  );
}

export default App;