import React from "react";

function AIExplanationPanel({ explanation }) {
  if (!explanation) return null;

  const {
    summary,
    why_it_matters,
    potential_impact,
    recommended_fix,
    best_practice,
    cached,
    model_used,
  } = explanation;

  return (
    <div className="ai-explanation-panel" aria-label="AI security explanation content">
      <div className="ai-explanation-header">
        <span className="ai-badge">🤖 AI Security Analysis</span>
        <div className="ai-meta">
          {cached && <span className="cached-badge">⚡ cached</span>}
          <span className="model-badge">{model_used}</span>
        </div>
      </div>

      <div className="ai-sections-grid">
        {/* Section 1: Summary */}
        <div className="ai-section">
          <div className="ai-section-title">🔍 What is the problem?</div>
          <p className="ai-section-content">{summary}</p>
        </div>

        {/* Section 2: Why it matters */}
        <div className="ai-section">
          <div className="ai-section-title">⚠️ Why does it matter?</div>
          <p className="ai-section-content">{why_it_matters}</p>
        </div>

        {/* Section 3: Potential impact */}
        <div className="ai-section">
          <div className="ai-section-title">💥 Potential impact</div>
          <p className="ai-section-content">{potential_impact}</p>
        </div>

        {/* Section 4: Recommended fix */}
        <div className="ai-section highlighted">
          <div className="ai-section-title">🛠️ Recommended fix</div>
          <p className="ai-section-content fix-code-desc">{recommended_fix}</p>
        </div>

        {/* Section 5: Best practice */}
        <div className="ai-section">
          <div className="ai-section-title">💡 Security best practice</div>
          <p className="ai-section-content">{best_practice}</p>
        </div>
      </div>
    </div>
  );
}

export default AIExplanationPanel;
