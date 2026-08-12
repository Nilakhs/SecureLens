import os
import logging
from sqlalchemy.orm import Session
from app.ai.snippet_extractor import SnippetExtractor
from app.ai.prompt_builder import PromptBuilder
from app.ai.llm_client import LLMClient, LLMInvalidResponseError
from app.ai.cache import ExplanationCache
from app.models.ai_explanation import AIExplanation

logger = logging.getLogger(__name__)


def _resolve_file_path(project_path: str | None, finding_file: str) -> str | None:
    """
    Safely resolve the on-disk path for a finding's source file.
    Handles the case where finding_file already contains the full project_path
    prefix (which would cause a doubled path if naively os.path.join'd).
    """
    if not project_path or not finding_file:
        return None
    proj = os.path.normpath(project_path)
    ffile = os.path.normpath(finding_file)
    if os.path.isabs(ffile):
        return ffile
    # If the normalized finding path already starts with the project path,
    # use it directly (avoids: project_path/project_path/file.py)
    if ffile.startswith(proj + os.sep) or ffile == proj:
        return ffile
    return os.path.join(proj, ffile)


class ExplanationService:
    """
    Coordinates snippet extraction, prompt compiling, LLM calling, validating, and caching.
    The primary service layer for security explanations.
    """

    REQUIRED_KEYS = {
        "summary",
        "why_it_matters",
        "potential_impact",
        "recommended_fix",
        "best_practice"
    }

    @classmethod
    def explain(cls, finding: dict, project_path: str | None = None, db: Session | None = None) -> dict:
        """
        Generates an AI explanation for a single vulnerability finding.
        Utilizes both in-memory cache and PostgreSQL database persistence.

        Args:
            finding: The normalized finding dictionary.
            project_path: Optional path to the extracted project on disk.
            db: Optional database session to check and persist DB records.

        Returns:
            dict matching the AIExplanation schema.

        Raises:
            LLMError subclasses on failure.
        """
        finding_id = finding.get("id")

        # Resolve the actual file path on disk (if project_path is provided)
        file_path = _resolve_file_path(project_path, finding.get("file", ""))

        # 1. Best-effort extract code snippet
        line_number = finding.get("line", 0)
        snippet = None
        if file_path and line_number > 0:
            try:
                snippet = SnippetExtractor.extract(file_path, line_number)
            except Exception as e:
                logger.error(f"ExplanationService: Snippet extraction failed for {file_path}: {e}")

        # 2. Check in-memory Cache first
        cache_key = ExplanationCache.make_key(finding, snippet)
        cached_result = ExplanationCache.get(cache_key)
        if cached_result:
            logger.info("ExplanationService: In-memory cache hit. Returning cached explanation.")
            result = dict(cached_result)
            result["cached"] = True
            return result

        # 3. Check Database if finding_id is present
        if db and finding_id:
            try:
                db_explanation = db.query(AIExplanation).filter(AIExplanation.finding_id == finding_id).first()
                if db_explanation:
                    logger.info(f"ExplanationService: DB hit for finding_id {finding_id}. Loading into memory cache.")
                    result = {
                        "summary":          db_explanation.summary,
                        "why_it_matters":   db_explanation.why_it_matters,
                        "potential_impact": db_explanation.potential_impact,
                        "recommended_fix":  db_explanation.recommended_fix,
                        "best_practice":    db_explanation.best_practice,
                        "cached":           True,
                        "model_used":       db_explanation.model,
                    }
                    # Populate in-memory cache for future fast reads
                    ExplanationCache.set(cache_key, result)
                    return result
            except Exception as db_err:
                logger.error(f"ExplanationService: Database query failed: {db_err}")

        # 4. Build Prompt
        prompt = PromptBuilder.build(finding, snippet)
        system_instruction = PromptBuilder.SYSTEM_INSTRUCTION

        # 5. Request generation from LLM (propagates LLMError subclasses)
        raw_response = LLMClient.complete(prompt, system_instruction)

        # 6. Validate the structured response
        if not isinstance(raw_response, dict):
            logger.error(f"ExplanationService: Response is not a dict: {raw_response}")
            raise LLMInvalidResponseError("LLM response did not return a structured JSON object.")

        # Check for missing keys
        missing_keys = cls.REQUIRED_KEYS - raw_response.keys()
        if missing_keys:
            logger.error(f"ExplanationService: Response missing keys {missing_keys}: {raw_response}")
            raise LLMInvalidResponseError(
                f"LLM response structure was invalid. Missing fields: {', '.join(missing_keys)}"
            )

        # Build clean output
        model_name = os.getenv("AI_MODEL", "gemini-2.5-flash")
        explanation = {
            "summary":          str(raw_response["summary"]).strip(),
            "why_it_matters":   str(raw_response["why_it_matters"]).strip(),
            "potential_impact": str(raw_response["potential_impact"]).strip(),
            "recommended_fix":  str(raw_response["recommended_fix"]).strip(),
            "best_practice":    str(raw_response["best_practice"]).strip(),
            "cached":           False,
            "model_used":       model_name,
        }

        # 7. Save to Database if db and finding_id are available
        if db and finding_id:
            try:
                db_explanation = AIExplanation(
                    finding_id=finding_id,
                    model=model_name,
                    summary=explanation["summary"],
                    why_it_matters=explanation["why_it_matters"],
                    potential_impact=explanation["potential_impact"],
                    recommended_fix=explanation["recommended_fix"],
                    best_practice=explanation["best_practice"]
                )
                db.add(db_explanation)
                db.commit()
                logger.info(f"ExplanationService: Persisted explanation for finding_id {finding_id} to DB.")
            except Exception as db_save_err:
                db.rollback()
                logger.error(f"ExplanationService: Failed to save explanation to database: {db_save_err}")

        # 8. Save to in-memory Cache
        ExplanationCache.set(cache_key, explanation)

        return explanation
