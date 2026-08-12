from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.ai.explain_router import router as explain_router
from app.remediation.fix_router import router as fix_router
from app.api.history import router as history_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SecureLens API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(explain_router)
app.include_router(fix_router)
app.include_router(history_router)


@app.get("/")
def home():
    return {"message": "SecureLens Backend Running"}

