import { useState } from "react";
import UploadForm from "./components/UploadForm";
import ScanSummary from "./components/ScanSummary";
import HealthScoreCard from "./components/HealthScoreCard";
import InsightsPanel from "./components/InsightsPanel";
import GroupedFindings from "./components/GroupedFindings";
import FindingsTable from "./components/FindingsTable";
import ProjectDashboard from "./components/ProjectDashboard";
import "./App.css";

function App() {
  const [scanResult, setScanResult] = useState(null);
  const [activeView, setActiveView] = useState("grouped"); // "grouped" | "flat"

  const handleScanComplete = (data) => {
    setScanResult(data);
    setActiveView("grouped");
    setTimeout(() => {
      document.getElementById("results-section")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  const handleReset = () => {
    setScanResult(null);
  };

  return (
    <div className="app-wrapper">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-block">
            <span className="logo-icon">🔒</span>
            <span className="logo-text">SecureLens</span>
          </div>
          <p className="header-tagline">
            AI-Powered Source Code Vulnerability Scanner
          </p>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="app-main">
        {/* Upload — always visible */}
        <section className="upload-card" aria-label="Upload project">
          <h2 className="section-title">Upload Your Project</h2>
          <p className="section-sub">
            Upload a ZIP of your source code. SecureLens runs{" "}
            <strong>Semgrep</strong> and <strong>Bandit</strong>, then
            analyzes the results with its own Intelligence Engine.
          </p>
          <UploadForm onScanComplete={handleScanComplete} />
        </section>

        {/* Results — shown after scan */}
        {scanResult && (
          <div id="results-section" className="results-wrapper">

            {/* 1. Health Score — hero card */}
            <HealthScoreCard intelligence={scanResult.intelligence} />

            {/* 2. Scan Summary — scanners + severity counts */}
            <ScanSummary
              summary={scanResult.summary}
              scanId={scanResult.scan_id}
              scanStarted={scanResult.scan_started}
              scanFinished={scanResult.scan_finished}
              durationSeconds={scanResult.scan_duration_seconds}
            />

            {/* 3. Insights */}
            <InsightsPanel intelligence={scanResult.intelligence} />

            {/* 4. Project Metadata */}
            <ProjectDashboard metadata={scanResult.metadata} />

            {/* 5. Findings — toggle between grouped and flat view */}
            <div className="view-toggle-row">
              <span className="view-toggle-label">Findings view:</span>
              <div className="view-toggle-buttons" role="group">
                <button
                  id="grouped-view-btn"
                  className={`view-btn ${activeView === "grouped" ? "active" : ""}`}
                  onClick={() => setActiveView("grouped")}
                >
                  📂 By Category
                </button>
                <button
                  id="flat-view-btn"
                  className={`view-btn ${activeView === "flat" ? "active" : ""}`}
                  onClick={() => setActiveView("flat")}
                >
                  📋 All Findings
                </button>
              </div>
            </div>

            {activeView === "grouped" ? (
              <GroupedFindings intelligence={scanResult.intelligence} />
            ) : (
              <FindingsTable findings={scanResult.findings} />
            )}

            {/* Scan again */}
            <div className="scan-again-row">
              <button
                id="scan-again-button"
                className="btn-secondary"
                onClick={handleReset}
              >
                ↺ Scan Another Project
              </button>
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="app-footer">
        <p>
          SecureLens · Powered by Semgrep &amp; Bandit ·
          Intelligence Engine v1.0
        </p>
      </footer>
    </div>
  );
}

export default App;
