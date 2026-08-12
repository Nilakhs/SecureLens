import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.ai.schemas import ExplainRequest, AIExplanation
from app.ai.explanation_service import ExplanationService
from app.ai.llm_client import (
    LLMUnavailableError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["AI Explanation"])


@router.post("/explain", response_model=AIExplanation)
def explain_finding(payload: ExplainRequest, db: Session = Depends(get_db)):
    """
    On-demand AI security explanation endpoint.
    Receives a single finding details and optional project location to return
    a developer-friendly, structured vulnerability explanation.
    """
    finding = payload.finding
    project_path = payload.project_path

    # Basic input check
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding details are required in the request body."
        )

    try:
        explanation = ExplanationService.explain(finding, project_path, db)
        return explanation

    except LLMUnavailableError as e:
        logger.error(f"Router explain: LLM Unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    except LLMTimeoutError as e:
        logger.error(f"Router explain: LLM Request Timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e)
        )

    except LLMRateLimitError as e:
        logger.error(f"Router explain: LLM Rate Limit: {e}")
        raise HTTPException(
            status_code=429,  # status.HTTP_429_TOO_MANY_REQUESTS
            detail=str(e)
        )

    except LLMInvalidResponseError as e:
        logger.error(f"Router explain: LLM Invalid Response Structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except LLMError as e:
        logger.error(f"Router explain: LLM General Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )

    except Exception as e:
        logger.critical(f"Router explain: Unhandled server crash: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )
