import os
import shutil
import zipfile
from datetime import datetime
from app.services.language_detector import LanguageDetector
from app.services.framework_detector import FrameworkDetector
from app.services.package_manager_detector import PackageManagerDetector
from app.services.important_files_detector import ImportantFilesDetector
from app.services.entry_point_detector import EntryPointDetector
from app.services.project_stats_detector import ProjectStatsDetector
from fastapi import HTTPException

UPLOAD_FOLDER = "app/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class ProjectAnalyzer:

    @staticmethod
    async def analyze(file):
        # Check if file is a ZIP
        if not file.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

        # Read file contents
        contents = await file.read()

        # Reject empty ZIP files
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded ZIP file is empty.")

        # Reject files larger than 100 MB
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, detail="File size exceeds the 100 MB limit."
            )

        # Reset the file pointer
        await file.seek(0)

        # Create unique folder for this upload
        scan_folder = datetime.now().strftime("scan_%Y%m%d_%H%M%S")
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

        # Find all files recursively
        files = []

        for root, dirs, filenames in os.walk(extract_path):
            for filename in filenames:
                file_path = os.path.relpath(os.path.join(root, filename), extract_path)
                files.append(file_path)
        languages = LanguageDetector.detect(files)
        frameworks = FrameworkDetector.detect(extract_path)
        package_managers = PackageManagerDetector.detect(extract_path)
        important_files = ImportantFilesDetector.detect(extract_path)
        entry_point = EntryPointDetector.detect(extract_path)
        project_stats = ProjectStatsDetector.detect(extract_path)
        metadata = {
            "project_name": os.path.splitext(file.filename)[0],
            "languages": languages,
            "frameworks": frameworks,
            "package_managers": package_managers,
            "entry_point": entry_point,
            "statistics": {
                "files": project_stats["file_count"],
                "folders": project_stats["folder_count"],
                "size_mb": round(len(contents) / (1024 * 1024), 2),
            },
            "important_files": [
                file for file, exists in important_files.items() if exists
            ],
        }
        return {"metadata": metadata, "message": "Project analyzed successfully"}
