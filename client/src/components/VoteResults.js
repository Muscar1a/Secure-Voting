// src/components/VoteResults.js
import React, { useState } from "react";
import axios from "axios";

export default function VoteResults() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchResults = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("/mixnet_and_tally");
      setResults(res.data.tally);
    } catch (e) {
      console.error(e);
      setError("Không thể tải kết quả. Vui lòng thử lại.");
    }
    setLoading(false);
  };

  return (
    <div style={{ marginTop: 20 }}>
      <button
        onClick={fetchResults}
        style={{
          padding: "8px 16px",
          backgroundColor: "#2563EB",
          color: "#fff",
          border: "none",
          borderRadius: 4,
          cursor: "pointer"
        }}
      >
        Xem tổng số vote
      </button>

      {loading && <p style={{ marginTop: 10 }}>Đang tải…</p>}
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
              <span>{count} phiếu</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
