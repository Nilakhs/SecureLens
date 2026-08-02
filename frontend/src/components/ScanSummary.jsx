const SEVERITY_CONFIG = {
  CRITICAL: { color: "sev-critical", icon: "🔴" },
  HIGH:     { color: "sev-high",     icon: "🟠" },
  MEDIUM:   { color: "sev-medium",   icon: "🟡" },
  LOW:      { color: "sev-low",      icon: "🔵" },
  INFO:     { color: "sev-info",     icon: "⚪" },
};

function ScanSummary({ summary, scanId, scanStarted, scanFinished, durationSeconds }) {
  if (!summary) return null;

  const { total_findings, critical, high, medium, low, info, scanners_run, scanners_status } =
    summary;

  const formatTime = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleTimeString();
  };

  const statCards = [
    { label: "Total Findings", value: total_findings, cls: "stat-total" },
    { label: "Critical",       value: critical,       cls: "sev-critical" },
    { label: "High",           value: high,           cls: "sev-high" },
    { label: "Medium",         value: medium,         cls: "sev-medium" },
    { label: "Low",            value: low,            cls: "sev-low" },
    { label: "Info",           value: info,           cls: "sev-info" },
  ];

  return (
    <section className="scan-summary-section" aria-label="Scan Summary">
      {/* Header row */}
      <div className="scan-header">
        <div className="scan-id-block">
          <span className="scan-id-label">SCAN ID</span>
          <span className="scan-id-value">{scanId}</span>
        </div>

        <div className="scan-timing">
          <span>⏱ Started: {formatTime(scanStarted)}</span>
          <span>⏱ Finished: {formatTime(scanFinished)}</span>
          <span>⌛ Duration: {durationSeconds}s</span>
        </div>
      </div>

      {/* Scanners status row */}
      <div className="scanners-row">
        <span className="scanners-label">Scanners:</span>
        {scanners_run.map((name) => {
          const status = scanners_status?.[name] ?? "unknown";
          const ok = status === "success";
          return (
            <span
              key={name}
              className={`scanner-chip ${ok ? "chip-ok" : "chip-fail"}`}
              title={status}
            >
              {ok ? "✓" : "✗"} {name.charAt(0).toUpperCase() + name.slice(1)}
            </span>
          );
        })}
      </div>

      {/* Stat cards */}
      <div className="stat-cards-grid">
        {statCards.map(({ label, value, cls }) => (
          <div key={label} className={`stat-card ${cls}`}>
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default ScanSummary;
