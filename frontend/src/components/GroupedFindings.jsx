import { useState } from "react";

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

function FindingMiniRow({ finding }) {
  const [open, setOpen] = useState(false);
  return (
    <>
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
      {open && (
        <tr className="finding-detail-row">
          <td colSpan={5}>
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
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function GroupAccordion({ group, recommendation }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`group-accordion ${open ? "open" : ""}`}>
      {/* Group header — always visible */}
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

      {/* Group body — shown when expanded */}
      {open && (
        <div className="group-body" role="region">

          {/* Recommendation */}
          {recommendation && (
            <div className="group-recommendation">
              <span className="rec-icon">💡</span>
              <p>{recommendation}</p>
            </div>
          )}

          {/* Affected files summary */}
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

function GroupedFindings({ intelligence }) {
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
          // Get full group with findings from grouped_findings dict
          const fullGroup = grouped_findings?.[category] ?? groupSummary;
          const recommendation = recommendations?.[category];

          return (
            <GroupAccordion
              key={category}
              group={fullGroup}
              recommendation={recommendation}
            />
          );
        })}
      </div>
    </section>
  );
}

export default GroupedFindings;
