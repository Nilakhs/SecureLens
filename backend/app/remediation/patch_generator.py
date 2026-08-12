import json
import logging
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTION = """You are a secure code remediation assistant.

A security scanner identified a vulnerability in source code. Your task is to propose a MINIMAL, SAFE fix.

You MUST respond with a JSON object exactly matching this schema:
{
  "fixed_code": "The corrected code block (only the lines provided — do not invent new files or imports unless strictly necessary)",
  "explanation": "Clear plain-language explanation of what vulnerability existed and what changes address it",
  "changes": ["bullet 1 describing one specific change", "bullet 2 describing another change"],
  "limitations": "Any assumptions made, edge cases not covered, or things the developer must verify manually"
}

STRICT RULES — you MUST follow all of these:
1. Preserve existing functionality. Only change what is necessary to fix the security issue.
2. Do NOT rewrite unrelated code outside the provided snippet.
3. Do NOT invent imports, dependencies, or functions not already present.
4. Do NOT remove existing security checks or validations.
5. Do NOT add placeholder comments like "# TODO: implement this".
6. Keep changes minimal and reviewable.
7. Return ONLY raw JSON — no markdown code fences, no explanation outside JSON.
8. The fixed_code must be a valid replacement for the original snippet lines provided.
"""


class PatchGenerator:
    """
    Calls the LLM to generate a minimal, structured security fix for a finding.
    """

    @staticmethod
    def generate(finding: dict, snippet: dict | None) -> dict:
        """
        Build and send the remediation prompt. Returns the raw AI response dict.

        Args:
            finding: The normalized finding dictionary.
            snippet: The extracted code snippet dict (or None).

        Returns:
            Raw dict from LLM with keys: fixed_code, explanation, changes, limitations
        """
        metadata = {
            "category":            finding.get("category", "Unknown"),
            "severity":            finding.get("severity", "LOW"),
            "priority":            finding.get("priority", "LOW"),
            "rule_id":             finding.get("rule_id", "Unknown"),
            "scanner":             finding.get("scanner", "Unknown"),
            "finding_title":       finding.get("title", "Unknown"),
            "finding_description": finding.get("description", "No description available."),
            "file":                finding.get("file", "Unknown"),
            "line":                finding.get("line", 0),
            "cwe":                 finding.get("cwe", []),
        }

        prompt_data = {"finding": metadata}

        if snippet:
            prompt_data["code_to_fix"] = {
                "start_line": snippet["start_line"],
                "end_line":   snippet["end_line"],
                "code":       snippet["code"],
            }
        else:
            prompt_data["code_to_fix"] = "No source code context available. Provide a general fix pattern for this category."

        prompt = json.dumps(prompt_data, indent=2)

        logger.info(f"PatchGenerator: Requesting fix for {finding.get('category')} in {finding.get('file')}:{finding.get('line')}")
        return LLMClient.complete(prompt, SYSTEM_INSTRUCTION)
