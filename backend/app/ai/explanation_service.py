import os
import logging
from app.ai.snippet_extractor import SnippetExtractor
from app.ai.prompt_builder import PromptBuilder
from app.ai.llm_client import LLMClient, LLMInvalidResponseError
from app.ai.cache import ExplanationCache

logger = logging.getLogger(__name__)


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
    def explain(cls, finding: dict, project_path: str | None = None) -> dict:
        """
        Generates an AI explanation for a single vulnerability finding.

        Args:
            finding: The normalized finding dictionary.
            project_path: Optional path to the extracted project on disk.

        Returns:
            dict matching the AIExplanation schema.

        Raises:
            LLMError subclasses on failure.
        """
        # Resolve the actual file path on disk (if project_path is provided)
        file_path = None
        if project_path and finding.get("file"):
            # Check if finding's file is absolute or relative
            finding_file = finding["file"]
            if os.path.isabs(finding_file):
                file_path = finding_file
            else:
                file_path = os.path.join(project_path, finding_file)

        # 1. Best-effort extract code snippet
        line_number = finding.get("line", 0)
        snippet = None
        if file_path and line_number > 0:
            try:
                snippet = SnippetExtractor.extract(file_path, line_number)
            except Exception as e:
                logger.error(f"ExplanationService: Snippet extraction failed for {file_path}: {e}")

        # 2. Check Cache
        cache_key = ExplanationCache.make_key(finding, snippet)
        cached_result = ExplanationCache.get(cache_key)
        if cached_result:
            logger.info("ExplanationService: Cache hit. Returning cached explanation.")
            # Set cached=True on the returned copy, but keep cached=False in the store
            result = dict(cached_result)
            result["cached"] = True
            return result

        # 3. Build Prompt
        prompt = PromptBuilder.build(finding, snippet)
        system_instruction = PromptBuilder.SYSTEM_INSTRUCTION

        # 4. Request generation from LLM (propagates LLMError subclasses)
        raw_response = LLMClient.complete(prompt, system_instruction)

        # 5. Validate the structured response
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

        # 6. Cache the output
        ExplanationCache.set(cache_key, explanation)

        return explanation
