import { useState } from "react";

const GRADE_CONFIG = {
  "A+": { color: "grade-a-plus", bg: "#064e3b", text: "#6ee7b7" },
  "A":  { color: "grade-a",      bg: "#064e3b", text: "#6ee7b7" },
  "B+": { color: "grade-b-plus", bg: "#1e3a5f", text: "#93c5fd" },
  "B":  { color: "grade-b",      bg: "#1e3a5f", text: "#93c5fd" },
  "C+": { color: "grade-c-plus", bg: "#422006", text: "#fde68a" },
  "C":  { color: "grade-c",      bg: "#422006", text: "#fde68a" },
  "D":  { color: "grade-d",      bg: "#431407", text: "#fdba74" },
  "F":  { color: "grade-f",      bg: "#3b0a0a", text: "#fca5a5" },
};

function ScoreRing({ score }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const filled = circumference - (score / 100) * circumference;

  const color =
    score >= 80 ? "#22c55e" :
    score >= 60 ? "#eab308" :
    score >= 40 ? "#f97316" :
    "#ef4444";

  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="score-ring-svg">
      {/* Track */}
      <circle
        cx="70" cy="70" r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="10"
      />
      {/* Progress */}
      <circle
        cx="70" cy="70" r={radius}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={filled}
        transform="rotate(-90 70 70)"
        style={{ transition: "stroke-dashoffset 1s ease-out" }}
      />
      {/* Score number */}
      <text x="70" y="66" textAnchor="middle" fill={color}
        fontSize="28" fontWeight="700" fontFamily="Inter, sans-serif">
        {score}
      </text>
      <text x="70" y="84" textAnchor="middle" fill="rgba(255,255,255,0.4)"
        fontSize="11" fontFamily="Inter, sans-serif">
        / 100
      </text>
    </svg>
  );
}

function HealthScoreCard({ intelligence }) {
  const [showDeductions, setShowDeductions] = useState(false);

  if (!intelligence) return null;

  const { health_score, grade, score_deductions, total_deducted } = intelligence;
  const gradeCfg = GRADE_CONFIG[grade] ?? GRADE_CONFIG["F"];

  return (
    <section className="health-card" aria-label="Project Health Score">
      <div className="health-card-inner">

        {/* Left — Score ring */}
        <div className="health-score-block">
          <ScoreRing score={health_score} />
          <p className="health-label">Health Score</p>
        </div>

        {/* Centre — Grade + message */}
        <div className="health-grade-block">
          <div
            className="grade-badge-large"
            style={{ background: gradeCfg.bg, color: gradeCfg.text }}
            aria-label={`Grade ${grade}`}
          >
            {grade}
          </div>
          <p className="grade-message">
            {health_score >= 90 && "Excellent security posture 🏆"}
            {health_score >= 80 && health_score < 90 && "Good — a few things to tighten up 👍"}
            {health_score >= 70 && health_score < 80 && "Moderate risk — address high findings soon ⚠"}
            {health_score >= 50 && health_score < 70 && "Significant issues found — action needed 🔥"}
            {health_score <  50 && "Critical risk — immediate remediation required 🚨"}
          </p>
          <p className="deducted-note">
            {total_deducted > 0
              ? `${total_deducted} points deducted from 100`
              : "No deductions — clean project!"}
          </p>
        </div>

        {/* Right — Deductions breakdown */}
        <div className="health-deductions-block">
          <button
            className="deductions-toggle"
            onClick={() => setShowDeductions((p) => !p)}
            aria-expanded={showDeductions}
          >
            {showDeductions ? "▲ Hide breakdown" : "▼ Score breakdown"}
          </button>

          {showDeductions && (
            <div className="deductions-list" aria-label="Score deductions">
              {score_deductions.length === 0 ? (
                <p className="empty-text">No deductions.</p>
              ) : (
                score_deductions.map((d) => (
                  <div key={d.category} className="deduction-row">
                    <span className="deduction-category">{d.category}</span>
                    <span className="deduction-meta">
                      {d.count}× finding{d.count > 1 ? "s" : ""}
                    </span>
                    <span className="deduction-points">−{d.points}pts</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

      </div>
    </section>
  );
}

export default HealthScoreCard;
