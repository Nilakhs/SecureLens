from fastapi import FastAPI
from app.api.upload import router as upload_router

app = FastAPI(title="SecureLens API")

app.include_router(upload_router)


@app.get("/")
def home():
    return {"message": "SecureLens Backend Running"}
