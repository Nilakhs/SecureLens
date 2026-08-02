import { useState } from "react";

const ALL_SEVERITIES = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

const SEVERITY_CONFIG = {
  CRITICAL: { cls: "sev-critical", label: "CRITICAL" },
  HIGH:     { cls: "sev-high",     label: "HIGH" },
  MEDIUM:   { cls: "sev-medium",   label: "MEDIUM" },
  LOW:      { cls: "sev-low",      label: "LOW" },
  INFO:     { cls: "sev-info",     label: "INFO" },
};

function SeverityBadge({ severity }) {
  const cfg = SEVERITY_CONFIG[severity] ?? { cls: "sev-info", label: severity };
  return <span className={`severity-badge ${cfg.cls}`}>{cfg.label}</span>;
}

function ScannerChips({ detectedBy }) {
  if (!detectedBy?.length) return null;
  return (
    <span className="detected-by-chips">
      {detectedBy.map((s) => (
        <span key={s} className="scanner-chip chip-ok small">
          {s.charAt(0).toUpperCase() + s.slice(1)}
        </span>
      ))}
    </span>
  );
}

function FindingRow({ finding, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className={`finding-row ${expanded ? "expanded" : ""}`}
        onClick={() => setExpanded((prev) => !prev)}
        style={{ cursor: "pointer" }}
        aria-expanded={expanded}
      >
        <td>
          <SeverityBadge severity={finding.severity} />
        </td>
        <td className="file-cell" title={finding.file}>
          <code>{finding.file}</code>
        </td>
        <td className="line-cell">{finding.line}</td>
        <td>{finding.category}</td>
        <td>{finding.title}</td>
        <td>
          <ScannerChips detectedBy={finding.detected_by} />
        </td>
        <td className="expand-toggle">{expanded ? "▲" : "▼"}</td>
      </tr>

      {expanded && (
        <tr className="finding-detail-row">
          <td colSpan={7}>
            <div className="finding-detail">
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

              {finding.owasp?.length > 0 && (
                <div className="detail-section">
                  <strong>OWASP</strong>
                  <p>{finding.owasp.join(", ")}</p>
                </div>
              )}

              {finding.references?.length > 0 && (
                <div className="detail-section">
                  <strong>References</strong>
                  <ul className="ref-list">
                    {finding.references.map((ref, i) => (
                      <li key={i}>
                        <a href={ref} target="_blank" rel="noreferrer">
                          {ref}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="detail-section">
                <strong>Rule ID</strong>
                <code>{finding.rule_id}</code>
              </div>

              <div className="detail-section">
                <strong>Recommendation</strong>
                <p>{finding.recommendation}</p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function FindingsTable({ findings }) {
  const [activeFilter, setActiveFilter] = useState("ALL");

  if (!findings) return null;

  const filtered =
    activeFilter === "ALL"
      ? findings
      : findings.filter((f) => f.severity === activeFilter);

  const countFor = (sev) =>
    sev === "ALL"
      ? findings.length
      : findings.filter((f) => f.severity === sev).length;

  return (
    <section className="findings-section" aria-label="Security Findings">
      <div className="findings-header">
        <h2 className="section-title">Security Findings</h2>

        {/* Severity filter pills */}
        <div className="filter-pills" role="group" aria-label="Filter by severity">
          {ALL_SEVERITIES.map((sev) => (
            <button
              key={sev}
              className={`filter-pill ${activeFilter === sev ? "active" : ""} ${
                sev !== "ALL" ? `pill-${sev.toLowerCase()}` : ""
              }`}
              onClick={() => setActiveFilter(sev)}
            >
              {sev} <span className="pill-count">{countFor(sev)}</span>
            </button>
          ))}
        </div>
      </div>

      {findings.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <h3>No vulnerabilities found!</h3>
          <p>Your project looks clean. Great work!</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h3>No {activeFilter} findings</h3>
          <p>No findings matched this severity filter.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="findings-table" aria-label="Findings table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>File</th>
                <th>Line</th>
                <th>Category</th>
                <th>Title</th>
                <th>Detected By</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((finding, i) => (
                <FindingRow
                  key={`${finding.file}-${finding.line}-${finding.rule_id}-${i}`}
                  finding={finding}
                  index={i}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default FindingsTable;
