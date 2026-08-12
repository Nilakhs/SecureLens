from pydantic import BaseModel, Field
from typing import Optional, List


class ExplainRequest(BaseModel):
    finding: dict = Field(..., description="The full finding dict representation")
    project_path: Optional[str] = Field(None, description="Optional path to the extracted project on disk")


class AIExplanation(BaseModel):
    summary: str = Field(..., description="What is the problem?")
    why_it_matters: str = Field(..., description="Why is it dangerous?")
    potential_impact: str = Field(..., description="What could happen if exploited?")
    recommended_fix: str = Field(..., description="How to fix it?")
    best_practice: str = Field(..., description="What security principle/best practice applies?")
    cached: bool = Field(False, description="Whether this response was served from cache")
    model_used: str = Field(..., description="The name of the LLM model used")
