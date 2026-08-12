import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.remediation.schemas import FixRequest, RemediationFix
from app.remediation.remediation_service import RemediationService
from app.ai.llm_client import (
    LLMUnavailableError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["AI Remediation"])


@router.post("/fix", response_model=RemediationFix)
def fix_finding(payload: FixRequest, db: Session = Depends(get_db)):
    """
    On-demand AI remediation endpoint.
    Generates a minimal, validated, diff-annotated security fix for a single finding.
    The original project is NEVER modified.
    """
    finding      = payload.finding
    project_path = payload.project_path

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding details are required."
        )

    try:
        fix = RemediationService.fix(finding, project_path, db)
        return fix

    except LLMUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMTimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMInvalidResponseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.critical(f"fix_router: Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")
