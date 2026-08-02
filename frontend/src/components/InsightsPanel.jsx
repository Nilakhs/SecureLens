const PRIORITY_CONFIG = {
  IMMEDIATE: { cls: "pri-immediate", label: "IMMEDIATE", icon: "🚨" },
  HIGH:      { cls: "pri-high",      label: "HIGH",      icon: "🔥" },
  MEDIUM:    { cls: "pri-medium",    label: "MEDIUM",    icon: "⚠" },
  LOW:       { cls: "pri-low",       label: "LOW",       icon: "ℹ" },
};

function InsightCard({ icon, label, value, sub }) {
  return (
    <div className="insight-card">
      <div className="insight-icon">{icon}</div>
      <div className="insight-body">
        <p className="insight-label">{label}</p>
        <p className="insight-value" title={value}>{value ?? "—"}</p>
        {sub && <p className="insight-sub">{sub}</p>}
      </div>
    </div>
  );
}

function PriorityBadge({ priority }) {
  const cfg = PRIORITY_CONFIG[priority] ?? { cls: "pri-low", label: priority, icon: "ℹ" };
  return (
    <span className={`priority-badge ${cfg.cls}`}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

function InsightsPanel({ intelligence }) {
  if (!intelligence) return null;

  const { insights, priority_counts, executive_summary } = intelligence;

  const priorityOrder = ["IMMEDIATE", "HIGH", "MEDIUM", "LOW"];

  return (
    <section className="insights-section" aria-label="Security Insights">
      <h2 className="section-title">Security Insights</h2>

      {/* Insight cards grid */}
      <div className="insights-grid">
        <InsightCard
          icon="🎯"
          label="Most Common Risk"
          value={insights.most_common_category ?? "None"}
          sub={
            insights.most_common_category_count > 0
              ? `${insights.most_common_category_count} occurrence${insights.most_common_category_count > 1 ? "s" : ""}`
              : null
          }
        />
        <InsightCard
          icon="📁"
          label="Most Affected Folder"
          value={insights.most_affected_folder ?? "None"}
          sub={
            insights.most_affected_folder_count > 0
              ? `${insights.most_affected_folder_count} finding${insights.most_affected_folder_count > 1 ? "s" : ""}`
              : null
          }
        />
        <InsightCard
          icon="⚠"
          label="Highest Risk File"
          value={
            insights.highest_risk_file
              ? insights.highest_risk_file.split(/[/\\]/).pop()
              : "None"
          }
          sub={
            insights.highest_risk_file_count > 0
              ? `${insights.highest_risk_file_count} finding${insights.highest_risk_file_count > 1 ? "s" : ""}`
              : null
          }
        />
        <InsightCard
          icon="🔍"
          label="Top Scanner"
          value={
            insights.scanner_with_most_findings
              ? insights.scanner_with_most_findings.charAt(0).toUpperCase() +
                insights.scanner_with_most_findings.slice(1)
              : "None"
          }
          sub={
            insights.scanner_finding_counts &&
            Object.entries(insights.scanner_finding_counts)
              .map(([s, c]) => `${s}: ${c}`)
              .join(" · ")
          }
        />
        <InsightCard
          icon="📄"
          label="Files Affected"
          value={String(insights.total_files_affected ?? 0)}
          sub={`out of ${executive_summary?.files_scanned ?? 0} scanned`}
        />
        <InsightCard
          icon="🚨"
          label="Immediate Actions"
          value={String(priority_counts?.IMMEDIATE ?? 0)}
          sub="findings needing urgent fix"
        />
      </div>

      {/* Priority breakdown bar */}
      {Object.values(priority_counts ?? {}).some((c) => c > 0) && (
        <div className="priority-breakdown">
          <p className="priority-breakdown-label">Action Priority Breakdown</p>
          <div className="priority-bars">
            {priorityOrder.map((p) => {
              const count = priority_counts?.[p] ?? 0;
              const cfg = PRIORITY_CONFIG[p];
              return (
                <div key={p} className="priority-bar-item">
                  <PriorityBadge priority={p} />
                  <span className="priority-bar-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}

export default InsightsPanel;
