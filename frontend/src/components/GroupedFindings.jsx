import { useState } from "react";
import AIExplanationPanel from "./AIExplanationPanel";
import RemediationPanel from "./RemediationPanel";

const API_BASE = "http://127.0.0.1:8000";

const SEVERITY_CONFIG = {
  CRITICAL: { cls: "sev-critical" },
  HIGH:     { cls: "sev-high" },
  MEDIUM:   { cls: "sev-medium" },
  LOW:      { cls: "sev-low" },
  INFO:     { cls: "sev-info" },
};

const PRIORITY_CONFIG = {
  IMMEDIATE: { cls: "pri-immediate", icon: "🚨" },
  HIGH:      { cls: "pri-high",      icon: "🔥" },
  MEDIUM:    { cls: "pri-medium",    icon: "⚠" },
  LOW:       { cls: "pri-low",       icon: "ℹ" },
};

function SeverityBadge({ severity }) {
  const cfg = SEVERITY_CONFIG[severity] ?? { cls: "sev-info" };
  return <span className={`severity-badge ${cfg.cls}`}>{severity}</span>;
}

function PriorityBadge({ priority }) {
  const cfg = PRIORITY_CONFIG[priority] ?? { cls: "pri-low", icon: "ℹ" };
  return (
    <span className={`priority-badge ${cfg.cls}`}>
      {cfg.icon} {priority}
    </span>
  );
}

// Maps HTTP status codes to human-readable messages
function getErrorMessage(status) {
  if (status === 503) return "AI service is unavailable. Check that AI_API_KEY is set in backend/.env.";
  if (status === 408) return "The explanation request timed out. Please try again.";
  if (status === 429) return "AI service is temporarily rate-limited. Please wait a moment and try again.";
  if (status === 422) return "The AI returned an unexpected response format. Please try again.";
  if (status === 502) return "Could not reach the AI service. Please try again later.";
  return "An unexpected error occurred. Please try again.";
}

function FindingMiniRow({ finding, projectPath }) {
  const [open, setOpen]               = useState(false);

  // Explain state
  const [aiState, setAiState]         = useState("idle");   // idle | loading | success | error
  const [explanation, setExplanation] = useState(null);
  const [errorMsg, setErrorMsg]       = useState("");

  // Fix state
  const [fixState, setFixState]       = useState("idle");   // idle | loading | success | error
  const [fix, setFix]                 = useState(null);
  const [fixErrorMsg, setFixErrorMsg] = useState("");

  async function handleExplain(e) {
    // Don't toggle the row open/closed when the button is clicked
    e.stopPropagation();

    // If we already have a successful explanation, toggle it instead of re-fetching
    if (aiState === "success") {
      setAiState("idle");
      setExplanation(null);
      return;
    }

    setAiState("loading");
    setExplanation(null);
    setErrorMsg("");

    try {
      const res = await fetch(`${API_BASE}/findings/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          finding:      finding,
          project_path: projectPath ?? null,
        }),
      });

      if (!res.ok) {
        const msg = getErrorMessage(res.status);
        setErrorMsg(msg);
        setAiState("error");
        return;
      }

      const data = await res.json();
      setExplanation(data);
      setAiState("success");
    } catch (err) {
      setErrorMsg("Network error: could not reach the backend. Make sure the backend server is running.");
      setAiState("error");
    }
  }

  async function handleFix(e) {
    e.stopPropagation();
    if (fixState === "success") {
      setFixState("idle");
      setFix(null);
      return;
    }
    setFixState("loading");
    setFix(null);
    setFixErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/findings/fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          finding:      finding,
          project_path: projectPath ?? null,
        }),
      });
      if (!res.ok) {
        setFixErrorMsg(getErrorMessage(res.status));
        setFixState("error");
        return;
      }
      const data = await res.json();
      setFix(data);
      setFixState("success");
    } catch (err) {
      setFixErrorMsg("Network error: could not reach the backend.");
      setFixState("error");
    }
  }

  return (
    <>
      {/* Main finding row */}
      <tr
        className={`mini-finding-row ${open ? "expanded" : ""}`}
        onClick={() => setOpen((p) => !p)}
        style={{ cursor: "pointer" }}
      >
        <td><SeverityBadge severity={finding.severity} /></td>
        <td className="file-cell"><code>{finding.file}</code></td>
        <td className="line-cell">{finding.line}</td>
        <td className="mini-title">{finding.title}</td>
        <td className="expand-toggle">{open ? "▲" : "▼"}</td>
      </tr>

      {/* Expanded detail row */}
      {open && (
        <tr className="finding-detail-row">
          <td colSpan={5}>
            <div className="finding-detail">
              {/* Existing detail sections */}
              <div className="detail-section">
                <strong>Description</strong>
                <p>{finding.description}</p>
              </div>
              {finding.cwe?.length > 0 && (
                <div className="detail-section">
                  <strong>CWE</strong>
                  <p>{finding.cwe.join(", ")}</p>
                </div>
              )}
              {finding.references?.length > 0 && (
                <div className="detail-section">
                  <strong>References</strong>
                  <ul className="ref-list">
                    {finding.references.map((r, i) => (
                      <li key={i}><a href={r} target="_blank" rel="noreferrer">{r}</a></li>
                    ))}
                  </ul>
                </div>
              )}

              {/* ── AI Explanation Section ── */}
              <div className="ai-explain-section">
                <div className="ai-action-buttons">
                  <button
                    className={`btn-explain-ai ${aiState === "success" ? "active" : ""}`}
                    onClick={handleExplain}
                    disabled={aiState === "loading"}
                    aria-label="Explain this finding with AI"
                  >
                    {aiState === "loading" && <span className="btn-spinner" aria-hidden="true" />}
                    {aiState === "idle"    && "🤖 Explain with AI"}
                    {aiState === "loading" && "Generating explanation…"}
                    {aiState === "success" && "✕ Hide Explanation"}
                    {aiState === "error"   && "🤖 Try Again"}
                  </button>

                  <button
                    className={`btn-generate-fix ${fixState === "success" ? "active" : ""}`}
                    onClick={handleFix}
                    disabled={fixState === "loading"}
                    aria-label="Generate a security fix with AI"
                  >
                    {fixState === "loading" && <span className="btn-spinner fix-spinner" aria-hidden="true" />}
                    {fixState === "idle"    && "🛠️ Generate Fix"}
                    {fixState === "loading" && "Generating fix…"}
                    {fixState === "success" && "✕ Hide Fix"}
                    {fixState === "error"   && "🛠️ Try Again"}
                  </button>
                </div>

                {/* Explain error */}
                {aiState === "error" && (
                  <div className="ai-error-box" role="alert">
                    <span className="ai-error-icon">⚠</span>
                    <p>{errorMsg}</p>
                  </div>
                )}

                {/* Explain loading */}
                {aiState === "loading" && (
                  <div className="ai-loading-box" aria-live="polite">
                    <div className="ai-loading-pulse" />
                    <p>Analyzing vulnerability with Gemini AI…</p>
                  </div>
                )}

                {/* Explain success */}
                {aiState === "success" && explanation && (
                  <AIExplanationPanel explanation={explanation} />
                )}

                {/* Fix error */}
                {fixState === "error" && (
                  <div className="ai-error-box" role="alert">
                    <span className="ai-error-icon">⚠</span>
                    <p>{fixErrorMsg}</p>
                  </div>
                )}

                {/* Fix loading */}
                {fixState === "loading" && (
                  <div className="ai-loading-box" aria-live="polite">
                    <div className="ai-loading-pulse fix-pulse" />
                    <p>Generating secure fix with Gemini AI…</p>
                  </div>
                )}

                {/* Fix success */}
                {fixState === "success" && fix && (
                  <RemediationPanel fix={fix} />
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function GroupAccordion({ group, recommendation, projectPath }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`group-accordion ${open ? "open" : ""}`}>
      {/* Group header */}
      <button
        className="group-header"
        onClick={() => setOpen((p) => !p)}
        aria-expanded={open}
      >
        <div className="group-header-left">
          <span className="group-name">{group.category}</span>
          <span className="group-count-badge">{group.count}</span>
          <SeverityBadge severity={group.worst_severity} />
          <PriorityBadge priority={group.worst_priority} />
        </div>
        <div className="group-header-right">
          <span className="group-files-hint">
            {group.files.length} file{group.files.length !== 1 ? "s" : ""}
          </span>
          <span className="group-chevron">{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {/* Group body */}
      {open && (
        <div className="group-body" role="region">
          {/* Recommendation */}
          {recommendation && (
            <div className="group-recommendation">
              <span className="rec-icon">💡</span>
              <p>{recommendation}</p>
            </div>
          )}

          {/* Affected files */}
          <div className="group-files-row">
            <span className="group-files-label">Affected files:</span>
            {group.files.map((f) => (
              <code key={f} className="group-file-chip">{f.split(/[/\\]/).pop()}</code>
            ))}
          </div>

          {/* Findings mini-table */}
          <div className="table-wrapper">
            <table className="findings-table mini-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>File</th>
                  <th>Line</th>
                  <th>Title</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {group.findings.map((f, i) => (
                  <FindingMiniRow
                    key={`${f.file}-${f.line}-${f.rule_id}-${i}`}
                    finding={f}
                    projectPath={projectPath}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function GroupedFindings({ intelligence, projectPath }) {
  if (!intelligence) return null;

  const { grouped_findings, groups_ordered, recommendations } = intelligence;

  if (!groups_ordered || groups_ordered.length === 0) {
    return (
      <section className="findings-section">
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <h3>No vulnerabilities found!</h3>
          <p>Your project looks clean. Great work!</p>
        </div>
      </section>
    );
  }

  return (
    <section className="findings-section" aria-label="Grouped Security Findings">
      <div className="findings-header">
        <h2 className="section-title">Vulnerabilities by Category</h2>
        <span className="groups-total-badge">
          {groups_ordered.length} categor{groups_ordered.length === 1 ? "y" : "ies"}
        </span>
      </div>

      <div className="groups-list">
        {groups_ordered.map((groupSummary) => {
          const category = groupSummary.category;
          const fullGroup = grouped_findings?.[category] ?? groupSummary;
          const recommendation = recommendations?.[category];

          return (
            <GroupAccordion
              key={category}
              group={fullGroup}
              recommendation={recommendation}
              projectPath={projectPath}
            />
          );
        })}
      </div>
    </section>
  );
}

export default GroupedFindings;
