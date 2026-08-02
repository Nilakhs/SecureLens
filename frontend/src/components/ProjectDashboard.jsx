const LANG_ICONS = {
  Python: "🐍", JavaScript: "🟨", TypeScript: "🔷", Java: "☕",
  "C++": "⚙️", "C#": "💜", Go: "🐹", PHP: "🐘", Ruby: "💎",
  Rust: "🦀", HTML: "🌐", CSS: "🎨", SQL: "🗄️", Kotlin: "🟣",
};

function MetaBadge({ label, value }) {
  if (!value) return null;
  return (
    <span className="meta-badge">
      <span className="meta-label">{label}</span>
      <span className="meta-value">{value}</span>
    </span>
  );
}

function ProjectDashboard({ metadata }) {
  if (!metadata) return null;

  const {
    project_name, languages, frameworks, package_managers,
    entry_point, statistics, important_files,
  } = metadata;

  const languageList = Object.entries(languages || {}).sort((a, b) => b[1] - a[1]);

  return (
    <section className="project-dashboard" aria-label="Project Overview">
      <h2 className="section-title">Project Overview</h2>

      {/* Top info row */}
      <div className="project-info-row">
        <div className="project-name-block">
          <span className="project-name-icon">📁</span>
          <span className="project-name-text">{project_name}</span>
        </div>

        <div className="project-badges">
          <MetaBadge label="Files"   value={statistics?.files} />
          <MetaBadge label="Folders" value={statistics?.folders} />
          <MetaBadge label="Size"    value={`${statistics?.size_mb} MB`} />
          {entry_point && (
            <MetaBadge label="Entry" value={entry_point} />
          )}
        </div>
      </div>

      {/* Detail cards row */}
      <div className="dashboard-cards">

        {/* Languages */}
        <div className="dash-card">
          <h3 className="dash-card-title">Languages</h3>
          <div className="lang-list">
            {languageList.length > 0 ? (
              languageList.map(([lang, count]) => (
                <div key={lang} className="lang-item">
                  <span className="lang-icon">{LANG_ICONS[lang] ?? "📄"}</span>
                  <span className="lang-name">{lang}</span>
                  <span className="lang-count">{count} files</span>
                </div>
              ))
            ) : (
              <p className="empty-text">None detected</p>
            )}
          </div>
        </div>

        {/* Frameworks */}
        <div className="dash-card">
          <h3 className="dash-card-title">Frameworks</h3>
          <div className="chip-list">
            {frameworks?.length > 0 ? (
              frameworks.map((fw) => (
                <span key={fw} className="info-chip">{fw}</span>
              ))
            ) : (
              <p className="empty-text">None detected</p>
            )}
          </div>
        </div>

        {/* Package Managers */}
        <div className="dash-card">
          <h3 className="dash-card-title">Package Managers</h3>
          <div className="chip-list">
            {package_managers?.length > 0 ? (
              package_managers.map((pm) => (
                <span key={pm} className="info-chip">{pm}</span>
              ))
            ) : (
              <p className="empty-text">None detected</p>
            )}
          </div>
        </div>

        {/* Important Files */}
        <div className="dash-card">
          <h3 className="dash-card-title">Important Files</h3>
          {important_files?.length > 0 ? (
            <ul className="file-list">
              {important_files.map((f) => (
                <li key={f} className="file-list-item">
                  <span className="file-icon">📄</span>
                  <code>{f}</code>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-text">None detected</p>
          )}
        </div>

      </div>
    </section>
  );
}

export default ProjectDashboard;
