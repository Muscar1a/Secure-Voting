// src/components/VoteResults.js
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function VoteResults() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();  // <-- thêm

  const fetchResults = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get("/results");
      setResults(res.data.tally);
    } catch (e) {
      console.error(e);
      setError("Cannot fetch results. Please try again later.");
    }
    setLoading(false);
  };

  return (
    <div style={{ marginTop: 20, maxWidth: 600, margin: "20px auto" }}>
      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={fetchResults}
          style={{
            flex: 1,
            padding: "8px 16px",
            backgroundColor: "#2563EB",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer"
          }}
        >
          Total Votes Results
        </button>

        <button
          onClick={() => navigate("/")}  // <-- xử lý chuyển về home
          style={{
            flex: 1,
            padding: "8px 16px",
            backgroundColor: "#4CAF50",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer"
          }}
        >
          Return to Home
        </button>
      </div>
      
      {loading && <p style={{ marginTop: 10 }}>Loading...</p>}
      {error && (
        <p style={{ marginTop: 10, color: "red" }}>
          {error}
        </p>
      )}

      {results && (
        <ul style={{ marginTop: 20, listStyle: "none", padding: 0 }}>
          {Object.entries(results).map(([candidate, count]) => (
            <li
              key={candidate}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "8px 0",
                borderBottom: "1px solid #eee"
              }}
            >
              <span>{candidate}</span>
              <span>{count} votes</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
