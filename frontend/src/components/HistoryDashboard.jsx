import React, { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";

function HistoryDashboard({ onScanSelect }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tracks which project's scan history is currently expanded
  const [expandedProjectId, setExpandedProjectId] = useState(null);
  const [scans, setScans] = useState([]);
  const [loadingScans, setLoadingScans] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  async function fetchProjects() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/history/projects`);
      if (!res.ok) throw new Error("Failed to load projects history.");
      const data = await res.json();
      setProjects(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleProjectClick(projectId) {
    if (expandedProjectId === projectId) {
      // Collapse
      setExpandedProjectId(null);
      setScans([]);
      return;
    }

    setExpandedProjectId(projectId);
    setLoadingScans(true);
    setScans([]);

    try {
      const res = await fetch(`${API_BASE}/history/projects/${projectId}/scans`);
      if (!res.ok) throw new Error("Failed to load project scans.");
      const data = await res.json();
      setScans(data.scans);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingScans(false);
    }
  }

  async function handleScanClick(scanId) {
    try {
      const res = await fetch(`${API_BASE}/history/scans/${scanId}`);
      if (!res.ok) throw new Error("Failed to load scan details.");
      const data = await res.json();
      onScanSelect(data);
    } catch (err) {
      alert("Error loading scan details: " + err.message);
    }
  }

  if (loading) {
    return (
      <div className="history-status-box" aria-live="polite">
        <div className="ai-loading-pulse" />
        <p>Loading projects history…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-status-box history-error-box" role="alert">
        <span>⚠</span>
        <p>{error}</p>
        <button onClick={fetchProjects} className="btn-secondary btn-retry">Retry</button>
      </div>
    );
  }

  return (
    <div className="history-container" aria-label="Projects and Scan History">
      <h2 className="section-title">Projects &amp; Scan History</h2>
      <p className="section-sub">
        Browse scanned projects, review previous scan performance, and see changes in security metrics over time.
      </p>

      {projects.length === 0 ? (
        <div className="empty-history-state">
          <div className="empty-icon">📂</div>
          <h3>No scanned projects yet</h3>
          <p>Scan a project in the "New Scan" tab to start building scan history.</p>
        </div>
      ) : (
        <div className="projects-history-list">
          {projects.map((proj) => {
            const isExpanded = expandedProjectId === proj.id;
            const hasScan = proj.last_scan;

            return (
              <div key={proj.id} className={`project-history-card ${isExpanded ? "expanded" : ""}`}>
                <div
                  className="project-history-header"
                  onClick={() => handleProjectClick(proj.id)}
                  style={{ cursor: "pointer" }}
                >
                  <div className="proj-header-left">
                    <span className="proj-folder-icon">📁</span>
                    <div>
                      <h3 className="proj-title">{proj.name}</h3>
                      <span className="proj-scans-count">
                        {proj.scan_count} scan{proj.scan_count !== 1 ? "s" : ""} conducted
                      </span>
                    </div>
                  </div>

                  <div className="proj-header-right">
                    {hasScan ? (
                      <div className="proj-last-scan-info">
                        <span className="last-scan-label">Last scan:</span>
                        <div className="last-scan-badge-group">
                          <span className={`grade-badge-mini grade-${proj.last_scan.grade.charAt(0)}`}>
                            {proj.last_scan.grade}
                          </span>
                          <span className="last-scan-score">{proj.last_scan.health_score}/100</span>
                        </div>
                      </div>
                    ) : (
                      <span className="no-scans-text">No scans</span>
                    )}
                    <span className="expanded-indicator">{isExpanded ? "▲" : "▼"}</span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="project-history-body">
                    {loadingScans ? (
                      <div className="scans-loading-spinner">
                        <div className="btn-spinner fix-spinner" />
                        <span>Fetching scan history…</span>
                      </div>
                    ) : scans.length === 0 ? (
                      <p className="no-scans-text">No scans found.</p>
                    ) : (
                      <div className="scans-table-wrapper">
                        <table className="scans-history-table">
                          <thead>
                            <tr>
                              <th>Scan Date</th>
                              <th>Scan ID</th>
                              <th>Status</th>
                              <th>Grade</th>
                              <th>Score</th>
                              <th>Findings</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {scans.map((scan) => {
                              const scanDate = new Date(scan.started_at).toLocaleString();
                              const isCompleted = scan.status === "COMPLETED";

                              return (
                                <tr key={scan.scan_id} className={`scan-row-${scan.status.toLowerCase()}`}>
                                  <td className="scan-date-cell">{scanDate}</td>
                                  <td className="scan-id-cell"><code>{scan.scan_id}</code></td>
                                  <td>
                                    <span className={`status-badge-mini status-${scan.status.toLowerCase()}`}>
                                      {scan.status}
                                    </span>
                                  </td>
                                  <td>
                                    {isCompleted ? (
                                      <span className={`grade-badge-mini grade-${scan.grade.charAt(0)}`}>
                                        {scan.grade}
                                      </span>
                                    ) : "—"}
                                  </td>
                                  <td className="score-cell">
                                    {isCompleted ? `${scan.health_score}/100` : "—"}
                                  </td>
                                  <td className="findings-cell">
                                    {isCompleted ? (
                                      <span className="findings-count-num">{scan.findings_count}</span>
                                    ) : "—"}
                                  </td>
                                  <td>
                                    {isCompleted ? (
                                      <button
                                        className="btn-view-scan"
                                        onClick={() => handleScanClick(scan.scan_id)}
                                      >
                                        🔍 View Results
                                      </button>
                                    ) : (
                                      <span className="scan-action-na">N/A</span>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default HistoryDashboard;
