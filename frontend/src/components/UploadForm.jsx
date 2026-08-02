import { useState } from "react";

// Scan state machine: idle → uploading → scanning → success | error
const STATES = {
  IDLE: "idle",
  UPLOADING: "uploading",
  SCANNING: "scanning",
  SUCCESS: "success",
  ERROR: "error",
};

function UploadForm({ onScanComplete }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [scanState, setScanState] = useState(STATES.IDLE);
  const [errorMessage, setErrorMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (file) => {
    if (file && file.name.toLowerCase().endsWith(".zip")) {
      setSelectedFile(file);
      setErrorMessage("");
    } else if (file) {
      setErrorMessage("Only ZIP files are accepted.");
    }
  };

  const handleInputChange = (e) => handleFileChange(e.target.files[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileChange(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select a ZIP file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      setScanState(STATES.UPLOADING);
      setErrorMessage("");

      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      setScanState(STATES.SCANNING);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setScanState(STATES.SUCCESS);
      onScanComplete(data);
    } catch (error) {
      setScanState(STATES.ERROR);
      setErrorMessage(error.message || "An unexpected error occurred.");
    }
  };

  const handleReset = () => {
    setScanState(STATES.IDLE);
    setSelectedFile(null);
    setErrorMessage("");
  };

  const isIdle    = scanState === STATES.IDLE;
  const isLoading = scanState === STATES.UPLOADING || scanState === STATES.SCANNING;

  return (
    <div className="upload-section">
      <div
        className={`upload-dropzone ${isDragging ? "dragging" : ""} ${selectedFile ? "has-file" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="upload-icon">
          {selectedFile ? "📦" : "☁️"}
        </div>

        {selectedFile ? (
          <div className="file-selected">
            <p className="file-name">{selectedFile.name}</p>
            <p className="file-size">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div className="upload-prompt">
            <p className="upload-title">Drop your project ZIP here</p>
            <p className="upload-subtitle">or click to browse files</p>
          </div>
        )}

        <input
          id="file-input"
          type="file"
          accept=".zip"
          className="file-input-hidden"
          onChange={handleInputChange}
          disabled={isLoading}
        />
        <label htmlFor="file-input" className="browse-label">
          Browse Files
        </label>
      </div>

      {errorMessage && (
        <div className="error-banner" role="alert">
          ⚠ {errorMessage}
        </div>
      )}

      {isLoading && (
        <div className="scan-progress">
          <div className="spinner" aria-hidden="true" />
          <div className="progress-text">
            {scanState === STATES.UPLOADING && "Uploading project..."}
            {scanState === STATES.SCANNING  && "Running security scanners (Semgrep + Bandit)..."}
          </div>
          <p className="progress-sub">This may take up to 2 minutes for large projects.</p>
        </div>
      )}

      <div className="upload-actions">
        <button
          id="scan-button"
          className="btn-primary"
          onClick={handleUpload}
          disabled={isLoading || !selectedFile}
        >
          {isLoading ? "Scanning..." : "🔍 Scan for Vulnerabilities"}
        </button>

        {(selectedFile || scanState !== STATES.IDLE) && !isLoading && (
          <button
            id="reset-button"
            className="btn-secondary"
            onClick={handleReset}
          >
            ↺ Reset
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadForm;
