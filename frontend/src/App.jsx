import { useState } from "react";
import UploadForm from "./components/UploadForm";
import ProjectDashboard from "./components/ProjectDashboard";
import "./App.css";

function App() {
  const [metadata, setMetadata] = useState(null);

  return (
    <div className="app">
      <header>
        <h1>🔒 SecureLens</h1>
        <p>AI-Powered Source Code Vulnerability Scanner</p>
      </header>

      <UploadForm onUploadSuccess={setMetadata} />

      {metadata && <ProjectDashboard metadata={metadata} />}
    </div>
  );
}

export default App;
