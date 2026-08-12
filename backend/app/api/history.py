import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.connection import get_db
from app.models.project import Project
from app.models.scan import Scan
from app.models.finding import Finding
from app.intelligence.intelligence_engine import IntelligenceEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["Scan History"])


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """Retrieve all projects with last scan summary and total scan count."""
    projects = db.query(Project).order_by(desc(Project.updated_at)).all()
    results = []

    for p in projects:
        # Get last completed scan
        last_scan = (
            db.query(Scan)
            .filter(Scan.project_id == p.id, Scan.status == "COMPLETED")
            .order_by(desc(Scan.started_at))
            .first()
        )

        total_scans = db.query(Scan).filter(Scan.project_id == p.id).count()

        last_scan_data = None
        if last_scan:
            total_findings = (
                last_scan.critical_count
                + last_scan.high_count
                + last_scan.medium_count
                + last_scan.low_count
                + last_scan.info_count
            )
            last_scan_data = {
                "scan_id":      last_scan.scan_id,
                "health_score": last_scan.health_score,
                "grade":        last_scan.grade,
                "findings":     total_findings,
                "date":         last_scan.started_at.isoformat(),
            }

        results.append({
            "id":          p.id,
            "name":        p.name,
            "created_at":  p.created_at.isoformat(),
            "updated_at":  p.updated_at.isoformat(),
            "scan_count":  total_scans,
            "last_scan":   last_scan_data,
        })

    return results


@router.get("/projects/{project_id}/scans")
def get_project_scans(project_id: int, db: Session = Depends(get_db)):
    """Retrieve all scans for a specific project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    scans = db.query(Scan).filter(Scan.project_id == project_id).order_by(desc(Scan.started_at)).all()
    results = []

    for s in scans:
        total_findings = (
            s.critical_count
            + s.high_count
            + s.medium_count
            + s.low_count
            + s.info_count
        )
        results.append({
            "id":               s.id,
            "scan_id":          s.scan_id,
            "status":           s.status,
            "started_at":       s.started_at.isoformat(),
            "finished_at":      s.finished_at.isoformat() if s.finished_at else None,
            "duration_seconds": s.duration_seconds,
            "health_score":     s.health_score,
            "grade":            s.grade,
            "findings_count":   total_findings,
            "scanners_used":    s.scanners_used,
        })

    return {
        "project": {
            "id":   project.id,
            "name": project.name,
        },
        "scans": list(results),
    }


@router.get("/scans/{scan_id}")
def get_scan_details(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve complete findings and intelligence analysis for a specific scan."""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found."
        )

    findings = db.query(Finding).filter(Finding.scan_id == scan.id).all()

    # Convert finding model records to dicts matching the frontend shape
    findings_list = []
    for f in findings:
        findings_list.append({
            "id":          f.id,
            "scanner":     f.scanner,
            "rule_id":     f.rule_id,
            "category":    f.category,
            "severity":    f.severity,
            "priority":    f.priority,
            "title":       f.title,
            "description": f.description,
            "file":        f.file,
            "line":        f.line,
            "cwe":         f.cwe,
            "owasp":       f.owasp,
        })

    # Reconstruct metadata (best effort from DB data)
    languages = {}
    for f in findings_list:
        ext = f["file"].split(".")[-1].lower() if "." in f["file"] else "other"
        if ext == "py":
            languages["Python"] = languages.get("Python", 0) + 1
        elif ext in ("js", "ts", "jsx", "tsx"):
            languages["JavaScript"] = languages.get("JavaScript", 0) + 1

    # Unique files affected
    unique_files = list({f["file"] for f in findings_list})

    metadata = {
        "project_name":     scan.project.name,
        "languages":        languages if languages else {"Python": 1},
        "frameworks":       [],
        "package_managers": [],
        "entry_point":      "unknown",
        "statistics": {
            "files":   len(unique_files),
            "folders": len(list({f["file"].split("/")[0] for f in findings_list if "/" in f["file"]})),
            "size_mb": 0.0,
        },
        "important_files": [],
    }

    # Re-analyze findings through the intelligence engine to dynamically build the
    # full dashboard data (health score, grade, insights, recommendations, groups, etc.)
    intelligence = IntelligenceEngine.analyze(findings_list, metadata)
    
    # Remove enriched_findings so it doesn't duplicate the findings list
    intelligence.pop("enriched_findings", None)

    summary = {
        "scanners_run": scan.scanners_used,
        "critical":     scan.critical_count,
        "high":         scan.high_count,
        "medium":       scan.medium_count,
        "low":          scan.low_count,
        "info":         scan.info_count,
        "total":        len(findings_list),
    }

    return {
        "scan_id":               scan.scan_id,
        "scan_started":          scan.started_at.isoformat(),
        "scan_finished":         scan.finished_at.isoformat() if scan.finished_at else None,
        "scan_duration_seconds": scan.duration_seconds,
        "metadata":              metadata,
        "summary":               summary,
        "findings":              findings_list,
        "intelligence":          intelligence,
        "project_path":          None,  # Not available for past scans unless stored, keep None
    }
