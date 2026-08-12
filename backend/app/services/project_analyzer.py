import os
import shutil
import zipfile
import random
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.language_detector import LanguageDetector
from app.services.framework_detector import FrameworkDetector
from app.services.package_manager_detector import PackageManagerDetector
from app.services.important_files_detector import ImportantFilesDetector
from app.services.entry_point_detector import EntryPointDetector
from app.services.project_stats_detector import ProjectStatsDetector
from app.scanners.scanner_manager import ScannerManager
from app.intelligence.intelligence_engine import IntelligenceEngine

from app.models.project import Project
from app.models.scan import Scan
from app.models.finding import Finding
from fastapi import HTTPException

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "app/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _generate_scan_id() -> str:
    """
    Generate a unique scan identifier in the format SCAN-YYYYMMDD-XXXX.
    Example: SCAN-20260812-4821
    """
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = f"{random.randint(1000, 9999)}"
    return f"SCAN-{date_str}-{suffix}"


class ProjectAnalyzer:

    @staticmethod
    async def analyze(file, db: Session):
        # ----------------------------------------------------------------
        # Validate upload
        # ----------------------------------------------------------------
        if not file.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

        contents = await file.read()

        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded ZIP file is empty.")

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, detail="File size exceeds the 100 MB limit."
            )

        await file.seek(0)

        # ----------------------------------------------------------------
        # Resolve Project in DB (Create if not exists)
        # ----------------------------------------------------------------
        project_name = os.path.splitext(file.filename)[0]
        try:
            db_project = db.query(Project).filter(Project.name == project_name).first()
            if not db_project:
                db_project = Project(name=project_name)
                db.add(db_project)
                db.commit()
                db.refresh(db_project)
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database error during project creation: {db_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Database configuration error during project initialization: {str(db_err)}"
            )

        # ----------------------------------------------------------------
        # Generate scan ID and start timestamp
        # ----------------------------------------------------------------
        scan_id = _generate_scan_id()
        scan_started = datetime.utcnow()

        # Create Scan record with RUNNING status
        try:
            db_scan = Scan(
                project_id=db_project.id,
                scan_id=scan_id,
                status="RUNNING",
                started_at=scan_started
            )
            db.add(db_scan)
            db.commit()
            db.refresh(db_scan)
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database error during scan initialization: {db_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error during scan initialization: {str(db_err)}"
            )

        # Run the scan inside a try-catch so we can record failure status in the DB
        try:
            # ----------------------------------------------------------------
            # Create isolated upload folder for this scan
            # ----------------------------------------------------------------
            scan_folder = scan_started.strftime("scan_%Y%m%d_%H%M%S")
            upload_path = os.path.join(UPLOAD_FOLDER, scan_folder)
            os.makedirs(upload_path, exist_ok=True)

            # Save the uploaded ZIP
            zip_path = os.path.join(upload_path, file.filename)
            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Extract the ZIP
            extract_path = os.path.join(upload_path, "extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            # ----------------------------------------------------------------
            # Metadata detection
            # ----------------------------------------------------------------
            files = []
            for root, dirs, filenames in os.walk(extract_path):
                for filename in filenames:
                    file_path = os.path.relpath(os.path.join(root, filename), extract_path)
                    files.append(file_path)

            languages       = LanguageDetector.detect(files)
            frameworks      = FrameworkDetector.detect(extract_path)
            package_managers = PackageManagerDetector.detect(extract_path)
            important_files = ImportantFilesDetector.detect(extract_path)
            entry_point     = EntryPointDetector.detect(extract_path)
            project_stats   = ProjectStatsDetector.detect(extract_path)

            metadata = {
                "project_name":    project_name,
                "languages":       languages,
                "frameworks":      frameworks,
                "package_managers": package_managers,
                "entry_point":     entry_point,
                "statistics": {
                    "files":   project_stats["file_count"],
                    "folders": project_stats["folder_count"],
                    "size_mb": round(len(contents) / (1024 * 1024), 2),
                },
                "important_files": [
                    f for f, exists in important_files.items() if exists
                ],
            }

            # ----------------------------------------------------------------
            # Security scanning — ScannerManager orchestrates all scanners
            # ----------------------------------------------------------------
            scan_result = ScannerManager.run(
                project_path=extract_path,
                scan_id=scan_id,
            )

            # ----------------------------------------------------------------
            # Intelligence Layer — categorize, prioritize, score, insights
            # ----------------------------------------------------------------
            intelligence = IntelligenceEngine.analyze(
                findings=scan_result["findings"],
                metadata=metadata,
            )

            # Patch executive summary with scanner info
            scanners_run = scan_result["summary"].get("scanners_run", [])
            intelligence["executive_summary"]["scanners_used"] = scanners_run

            # Use enriched findings as the final findings list
            final_findings = intelligence.pop("enriched_findings")

            # Calculate counts
            counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
            for f in final_findings:
                sev = str(f.get("severity", "INFO")).upper()
                if sev in counts:
                    counts[sev] += 1

            # ----------------------------------------------------------------
            # Finalize timing and update DB
            # ----------------------------------------------------------------
            scan_finished = datetime.utcnow()
            duration_seconds = round((scan_finished - scan_started).total_seconds(), 2)

            db_scan.status = "COMPLETED"
            db_scan.finished_at = scan_finished
            db_scan.duration_seconds = duration_seconds
            db_scan.health_score = intelligence["health_score"]
            db_scan.grade = intelligence["grade"]
            db_scan.critical_count = counts["CRITICAL"]
            db_scan.high_count = counts["HIGH"]
            db_scan.medium_count = counts["MEDIUM"]
            db_scan.low_count = counts["LOW"]
            db_scan.info_count = counts["INFO"]
            db_scan.scanners_used = scanners_run

            # Save each finding to DB
            for f in final_findings:
                db_finding = Finding(
                    scan_id=db_scan.id,
                    scanner=f.get("scanner", "unknown"),
                    rule_id=f.get("rule_id", "unknown"),
                    category=f.get("category", "Other"),
                    severity=f.get("severity", "INFO"),
                    priority=f.get("priority", "LOW"),
                    title=f.get("title", "unknown"),
                    description=f.get("description", ""),
                    file=f.get("file", ""),
                    line=f.get("line", 0),
                    cwe=f.get("cwe", []),
                    owasp=f.get("owasp", []),
                )
                db.add(db_finding)

            db.commit()

            # Map the database ID back into the findings list returned to the frontend
            # This allows subsequent explain/fix requests to know the exact DB finding ID
            for f, db_f in zip(final_findings, db_scan.findings):
                f["id"] = db_f.id

        except Exception as e:
            db.rollback()
            logger.critical(f"ProjectAnalyzer: Scan failed: {e}", exc_info=True)
            # Record FAILED status in DB
            try:
                db_scan.status = "FAILED"
                db_scan.finished_at = datetime.utcnow()
                db.commit()
            except Exception as db_err:
                logger.error(f"Failed to set scan status to FAILED in DB: {db_err}")
            raise e

        # ----------------------------------------------------------------
        # Build and return unified response
        # ----------------------------------------------------------------
        return {
            "scan_id":               scan_id,
            "scan_started":          scan_started.isoformat(),
            "scan_finished":         scan_finished.isoformat(),
            "scan_duration_seconds": duration_seconds,
            "metadata":              metadata,
            "summary":               scan_result["summary"],
            "findings":              final_findings,
            "intelligence":          intelligence,
            "project_path":          extract_path,
        }
