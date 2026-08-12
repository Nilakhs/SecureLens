import os
import shutil
import zipfile
import random
from datetime import datetime
from app.services.language_detector import LanguageDetector
from app.services.framework_detector import FrameworkDetector
from app.services.package_manager_detector import PackageManagerDetector
from app.services.important_files_detector import ImportantFilesDetector
from app.services.entry_point_detector import EntryPointDetector
from app.services.project_stats_detector import ProjectStatsDetector
from app.scanners.scanner_manager import ScannerManager
from app.intelligence.intelligence_engine import IntelligenceEngine
from fastapi import HTTPException

UPLOAD_FOLDER = "app/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _generate_scan_id() -> str:
    """
    Generate a unique scan identifier in the format SCAN-YYYYMMDD-XXXX.
    Example: SCAN-20260802-4821
    """
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = f"{random.randint(1000, 9999)}"
    return f"SCAN-{date_str}-{suffix}"


class ProjectAnalyzer:

    @staticmethod
    async def analyze(file):
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
        # Generate scan ID and start timestamp
        # ----------------------------------------------------------------
        scan_id = _generate_scan_id()
        scan_started = datetime.now()

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
            "project_name":    os.path.splitext(file.filename)[0],
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

        # Patch executive summary with scanner info (available here, not in engine)
        intelligence["executive_summary"]["scanners_used"] = (
            scan_result["summary"].get("scanners_run", [])
        )

        # Use enriched findings (with canonical category + priority) as the
        # canonical findings list going forward
        final_findings = intelligence.pop("enriched_findings")

        # ----------------------------------------------------------------
        # Finalize timing
        # ----------------------------------------------------------------
        scan_finished = datetime.now()
        duration_seconds = round((scan_finished - scan_started).total_seconds(), 2)

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
