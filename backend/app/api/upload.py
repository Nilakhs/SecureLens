import os
import zipfile
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_FOLDER = "app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

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
    extract_path = os.path.join(upload_path, "extracted")
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
    files = []
    for root, dirs, filenames in os.walk(extract_path):
        for filename in filenames:
            file_path = os.path.relpath(os.path.join(root, filename), extract_path)
            files.append(file_path)
    return {
        "project_name": os.path.splitext(file.filename)[0],
        "filename": file.filename,
        "size": len(contents),
        "saved_to": upload_path,
        "extracted_to": extract_path,
        "files": files,
        "message": "ZIP uploaded and extracted successfully",
    }
