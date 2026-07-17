from fastapi import APIRouter, UploadFile, File
from app.services.project_analyzer import ProjectAnalyzer

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return await ProjectAnalyzer.analyze(file)
