from pydantic import BaseModel, Field
from typing import Optional, List


class FixRequest(BaseModel):
    finding: dict = Field(..., description="Full finding dict from the frontend")
    project_path: Optional[str] = Field(None, description="Path to extracted project on disk")


class RemediationFix(BaseModel):
    original_code:       str          = Field(..., description="The code snippet that was analyzed")
    fixed_code:          str          = Field(..., description="AI proposed replacement code")
    explanation:         str          = Field(..., description="Plain-language explanation of what was changed and why")
    changes:             List[str]    = Field(..., description="Bullet-list of individual changes made")
    limitations:         str          = Field(..., description="What the AI warns it may have missed or assumed")
    diff:                str          = Field(..., description="Unified diff string showing before/after")
    syntax_valid:        bool         = Field(..., description="True if the fixed_code passed syntax validation")
    language:            str          = Field(..., description="Detected language: python, javascript, unknown")
    verification_status: str          = Field("UNVERIFIED", description="UNVERIFIED | VERIFIED | FAILED")
    cached:              bool         = Field(False)
    model_used:          str          = Field(...)
