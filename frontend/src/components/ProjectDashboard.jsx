function ProjectDashboard({ metadata }) {
  if (!metadata) return null;

  return (
    <div className="dashboard">
      <h2>Project Overview</h2>

      <div className="card">
        <h3>Project Name</h3>
        <p>{metadata.project_name}</p>
      </div>

      <div className="card">
        <h3>Languages</h3>
        <p>{Object.keys(metadata.languages).join(", ")}</p>
      </div>

      <div className="card">
        <h3>Frameworks</h3>
        <p>{metadata.frameworks.join(", ")}</p>
      </div>

      <div className="card">
        <h3>Package Managers</h3>
        <p>{metadata.package_managers.join(", ")}</p>
      </div>

      <div className="card">
        <h3>Files</h3>
        <p>{metadata.statistics.files}</p>
      </div>

      <div className="card">
        <h3>Folders</h3>
        <p>{metadata.statistics.folders}</p>
      </div>

      <div className="card">
        <h3>Project Size</h3>
        <p>{metadata.statistics.size_mb} MB</p>
      </div>

      <div className="card">
        <h3>Entry Point</h3>
        <p>{metadata.entry_point || "Not detected"}</p>
      </div>

      <div className="card">
        <h3>Important Files</h3>

        <ul>
          {metadata.important_files.map((file) => (
            <li key={file}>{file}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default ProjectDashboard;
