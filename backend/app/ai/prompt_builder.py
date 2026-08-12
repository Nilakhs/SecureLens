import json


class PromptBuilder:
    """
    Constructs a highly structured, controlled prompt for the LLM.
    Instructs the model to output a strict JSON structure containing the security explanation.
    """

    SYSTEM_INSTRUCTION = """You are an expert secure code review assistant.
Your task is to analyze the security finding details and the provided code snippet (if any) to explain the vulnerability to a developer.

You MUST respond with a JSON object. The response must follow this schema exactly:
{
  "summary": "Clear, concise 1-2 sentence description of what the security issue is in this specific code context.",
  "why_it_matters": "A concise explanation of why this vulnerability is dangerous and how it compromises security.",
  "potential_impact": "What an attacker could actually accomplish if they successfully exploit this (e.g. data breach, command execution, credentials theft).",
  "recommended_fix": "Clear, step-by-step developer instructions on how to remediate the issue, including secure coding alternatives or configurations.",
  "best_practice": "The fundamental security principle or best practice (e.g., OWASP, CWE guidelines) that developers should apply to avoid this class of vulnerability."
}

DO NOT wrap your JSON response in markdown code blocks like ```json ... ```. Just return raw JSON.
DO NOT invent facts that cannot be inferred from the provided code.
DO NOT claim that the application is exploitable in production unless the provided code snippet clearly supports that claim.
Keep all explanations developer-focused, professional, and clear.
"""

    @staticmethod
    def build(finding: dict, snippet: dict | None) -> str:
        """
        Builds the prompt string combining the finding metadata and the code snippet context.

        Args:
            finding: The normalized finding dictionary.
            snippet: The extracted snippet dictionary containing 'start_line', 'end_line', and 'code' (or None).

        Returns:
            The complete prompt string.
        """
        # Build metadata block
        metadata = {
            "category": finding.get("category", "Unknown"),
            "severity": finding.get("severity", "LOW"),
            "priority": finding.get("priority", "LOW"),
            "rule_id": finding.get("rule_id", "Unknown"),
            "scanner": finding.get("scanner", "Unknown"),
            "finding_title": finding.get("title", "Unknown"),
            "finding_description": finding.get("description", "No description available."),
            "file": finding.get("file", "Unknown"),
            "line": finding.get("line", 0),
            "cwe": finding.get("cwe", []),
            "owasp": finding.get("owasp", []),
        }

        prompt_data = {
            "finding_metadata": metadata,
        }

        if snippet:
            prompt_data["code_context"] = {
                "start_line": snippet["start_line"],
                "end_line": snippet["end_line"],
                "code": snippet["code"]
            }
        else:
            prompt_data["code_context"] = "No surrounding source code context is available for this file."

        # Return a cleanly formatted JSON string representing the prompt input
        return json.dumps(prompt_data, indent=2)
