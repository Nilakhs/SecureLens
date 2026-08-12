import difflib
import logging

logger = logging.getLogger(__name__)


class DiffGenerator:
    """
    Generates a unified diff between the original code snippet and the AI-proposed fix.
    Uses Python's built-in difflib — no extra dependencies required.
    """

    @staticmethod
    def generate(original_code: str, fixed_code: str, file_path: str = "original") -> str:
        """
        Produce a unified diff string.

        Args:
            original_code: The original source snippet.
            fixed_code:    The AI-proposed replacement.
            file_path:     File name for diff header labels.

        Returns:
            A unified diff string (empty string if no differences).
        """
        original_lines = original_code.splitlines(keepends=True)
        fixed_lines    = fixed_code.splitlines(keepends=True)

        # Ensure both end with newline for clean diffs
        if original_lines and not original_lines[-1].endswith("\n"):
            original_lines[-1] += "\n"
        if fixed_lines and not fixed_lines[-1].endswith("\n"):
            fixed_lines[-1] += "\n"

        diff_lines = list(difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        ))

        diff_str = "\n".join(diff_lines)
        logger.info(f"DiffGenerator: Generated diff with {len(diff_lines)} lines.")
        return diff_str
