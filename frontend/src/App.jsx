import { useState } from "react";
import UploadForm from "./components/UploadForm";
import ScanSummary from "./components/ScanSummary";
import FindingsTable from "./components/FindingsTable";
import ProjectDashboard from "./components/ProjectDashboard";
import "./App.css";

function App() {
  const [scanResult, setScanResult] = useState(null);

  const handleScanComplete = (data) => {
    setScanResult(data);
    // Smooth scroll to results
    setTimeout(() => {
      document.getElementById("results-section")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  const handleReset = () => setScanResult(null);

  return (
    <div className="app-wrapper">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-block">
            <span className="logo-icon">🔒</span>
            <span className="logo-text">SecureLens</span>
          </div>
          <p className="header-tagline">AI-Powered Source Code Vulnerability Scanner</p>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="app-main">

        {/* Upload section — always visible */}
        <section className="upload-card" aria-label="Upload project">
          <h2 className="section-title">Upload Your Project</h2>
          <p className="section-sub">
            Upload a ZIP of your source code. SecureLens will run{" "}
            <strong>Semgrep</strong> and <strong>Bandit</strong> and merge the results.
          </p>
          <UploadForm onScanComplete={handleScanComplete} />
        </section>

        {/* Results — shown after scan */}
        {scanResult && (
          <div id="results-section" className="results-wrapper">

            {/* Scan Summary */}
            <ScanSummary
              summary={scanResult.summary}
              scanId={scanResult.scan_id}
              scanStarted={scanResult.scan_started}
              scanFinished={scanResult.scan_finished}
              durationSeconds={scanResult.scan_duration_seconds}
            />

            {/* Project Metadata */}
            <ProjectDashboard metadata={scanResult.metadata} />

            {/* Findings Table */}
            <FindingsTable findings={scanResult.findings} />

            {/* Scan again button */}
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
        <p>SecureLens · Powered by Semgrep &amp; Bandit</p>
      </footer>
    </div>
  );
}

export default App;
