from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.project_analyzer import ProjectAnalyzer

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await ProjectAnalyzer.analyze(file, db)
