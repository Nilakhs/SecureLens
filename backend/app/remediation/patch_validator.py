import ast
import logging

logger = logging.getLogger(__name__)


def _detect_language(file_path: str | None) -> str:
    """Detect language from file extension."""
    if not file_path:
        return "unknown"
    lower = file_path.lower()
    if lower.endswith(".py"):
        return "python"
    if lower.endswith((".js", ".mjs", ".cjs")):
        return "javascript"
    if lower.endswith((".ts", ".tsx")):
        return "typescript"
    if lower.endswith((".java",)):
        return "java"
    if lower.endswith((".go",)):
        return "go"
    if lower.endswith((".rb",)):
        return "ruby"
    if lower.endswith((".php",)):
        return "php"
    return "unknown"


class PatchValidator:
    """
    Validates AI-generated fix code before presenting it to the user.
    Currently supports Python syntax validation via ast.parse().
    Other languages return syntax_valid=True with a note.
    """

    @staticmethod
    def validate(fixed_code: str, file_path: str | None) -> tuple[bool, str]:
        """
        Validate the fixed code for syntax correctness.

        Args:
            fixed_code: The AI-generated replacement code.
            file_path:  The original file path (used to determine language).

        Returns:
            Tuple of (syntax_valid: bool, language: str)
        """
        language = _detect_language(file_path)

        if not fixed_code or not fixed_code.strip():
            logger.warning("PatchValidator: fixed_code is empty.")
            return False, language

        if language == "python":
            try:
                ast.parse(fixed_code)
                logger.info("PatchValidator: Python AST parse passed.")
                return True, language
            except SyntaxError as e:
                logger.warning(f"PatchValidator: Python syntax error in fixed_code: {e}")
                return False, language
        else:
            # For other languages, we can't validate locally today
            logger.info(f"PatchValidator: No local validator for language '{language}'. Marking as valid.")
            return True, language
