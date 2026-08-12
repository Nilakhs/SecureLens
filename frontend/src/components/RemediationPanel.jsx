import { useState } from "react";

const STATUS_CONFIG = {
  VERIFIED:   { cls: "status-verified",   icon: "✅", label: "VERIFIED"   },
  FAILED:     { cls: "status-failed",     icon: "❌", label: "FIX FAILED" },
  UNVERIFIED: { cls: "status-unverified", icon: "⏳", label: "UNVERIFIED" },
};

function DiffView({ diff }) {
  if (!diff || !diff.trim()) {
    return (
      <p className="diff-empty">No changes detected in the diff.</p>
    );
  }

  const lines = diff.split("\n");

  return (
    <pre className="diff-block" aria-label="Before and after diff">
      {lines.map((line, i) => {
        let cls = "diff-line-ctx";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-line-add";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-line-del";
        else if (line.startsWith("@@")) cls = "diff-line-hunk";
        else if (line.startsWith("---") || line.startsWith("+++")) cls = "diff-line-header";
        return (
          <span key={i} className={cls}>
            {line}
            {"\n"}
          </span>
        );
      })}
    </pre>
  );
}

function RemediationPanel({ fix }) {
  const [showDiff, setShowDiff] = useState(true);

  if (!fix) return null;

  const {
    explanation,
    changes,
    limitations,
    diff,
    syntax_valid,
    language,
    verification_status,
    cached,
    model_used,
  } = fix;

  // Syntax-invalid fix — show rejection box and stop
  if (!syntax_valid) {
    return (
      <div className="remediation-panel syntax-error-panel">
        <div className="remediation-header">
          <span className="remediation-badge">🛠️ AI Suggested Fix</span>
        </div>
        <div className="syntax-error-box">
          <span className="syntax-error-icon">❌</span>
          <div>
            <strong>AI generated syntactically invalid {language} code.</strong>
            <p>This fix was automatically rejected. Review the vulnerability manually or try generating again.</p>
          </div>
        </div>
      </div>
    );
  }

  const statusCfg = STATUS_CONFIG[verification_status] ?? STATUS_CONFIG.UNVERIFIED;

  return (
    <div className="remediation-panel" aria-label="AI suggested fix">
      {/* Header */}
      <div className="remediation-header">
        <span className="remediation-badge">🛠️ AI Suggested Fix</span>
        <div className="remediation-meta">
          {cached && <span className="cached-badge">⚡ cached</span>}
          <span className={`verification-badge ${statusCfg.cls}`}>
            {statusCfg.icon} {statusCfg.label}
          </span>
          <span className="model-badge">{model_used}</span>
        </div>
      </div>

      {/* Safety warning — always visible */}
      <div className="ai-safety-warning">
        ⚠️ AI-generated code. Review carefully before applying to your project.
      </div>

      {/* Explanation */}
      <div className="remediation-section">
        <div className="remediation-section-title">📝 Explanation</div>
        <p className="remediation-section-content">{explanation}</p>
      </div>

      {/* Changes */}
      {changes?.length > 0 && (
        <div className="remediation-section">
          <div className="remediation-section-title">🔧 Changes Made</div>
          <ul className="changes-list">
            {changes.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Limitations */}
      {limitations && (
        <div className="remediation-section">
          <div className="remediation-section-title">⚠️ Limitations & Assumptions</div>
          <p className="remediation-section-content limitations-text">{limitations}</p>
        </div>
      )}

      {/* Diff toggle + view */}
      <div className="remediation-section diff-section">
        <div className="diff-header">
          <div className="remediation-section-title">📄 Before / After Diff</div>
          <button
            className="diff-toggle-btn"
            onClick={() => setShowDiff((p) => !p)}
          >
            {showDiff ? "Hide diff" : "Show diff"}
          </button>
        </div>
        {showDiff && <DiffView diff={diff} />}
      </div>

      {/* Verification status explanation */}
      <div className={`verification-note ${statusCfg.cls}`}>
        {verification_status === "VERIFIED" && (
          "SecureLens re-scanned the patched code and the original finding no longer appears. ✅"
        )}
        {verification_status === "FAILED" && (
          "SecureLens re-scanned the patched code and the vulnerability was still detected. Review the fix manually. ❌"
        )}
        {verification_status === "UNVERIFIED" && (
          "Verification scan could not be completed. Review the fix manually before applying."
        )}
      </div>
    </div>
  );
}

export default RemediationPanel;
