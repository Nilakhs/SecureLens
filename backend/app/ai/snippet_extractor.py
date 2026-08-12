import os
import logging

logger = logging.getLogger(__name__)


class SnippetExtractor:
    """
    Safely extracts a block of source code context centered around a specific line.
    Prevents reading very large files entirely, handles binary files and encoding errors gracefully.
    """

    @staticmethod
    def extract(file_path: str, line_number: int, context_lines: int = 10) -> dict | None:
        """
        Extract code context lines: [line_number - context_lines, line_number + context_lines].

        Args:
            file_path: Path to the target file.
            line_number: 1-indexed target line number.
            context_lines: Number of lines of context to include before and after.

        Returns:
            dict containing "start_line", "end_line", "code", or None if extraction failed.
        """
        if not file_path or not os.path.isfile(file_path):
            logger.warning(f"SnippetExtractor: File not found or invalid path: {file_path}")
            return None

        # Basic sanity check on lines
        if line_number <= 0:
            logger.warning(f"SnippetExtractor: Invalid line number {line_number} for {file_path}")
            return None

        # Exclude common compiled/binary files by extension to avoid processing them
        binary_extensions = {
            ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".bin", ".zip",
            ".tar", ".gz", ".rar", ".7z", ".png", ".jpg", ".jpeg", ".gif",
            ".pdf", ".db", ".sqlite", ".sqlite3", ".woff", ".woff2", ".ttf",
            ".eot", ".mp3", ".mp4", ".wav", ".avi", ".mov", ".class", ".jar"
        }
        _, ext = os.path.splitext(file_path.lower())
        if ext in binary_extensions:
            logger.warning(f"SnippetExtractor: Skipping potential binary file {file_path}")
            return None

        # Ensure we don't scan files that are way too large (e.g. minified JS, bulk data dumps)
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 2 * 1024 * 1024:  # > 2MB is suspicious for a source code file
                logger.warning(f"SnippetExtractor: Skipping large file ({file_size} bytes): {file_path}")
                return None
        except OSError as e:
            logger.warning(f"SnippetExtractor: Could not get file size of {file_path}: {e}")
            return None

        start_line = max(1, line_number - context_lines)
        end_line = line_number + context_lines

        lines_to_read = []
        try:
            # Open file safely using utf-8-sig to handle BOM or fallback to latin-1 on failure
            with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                # Read line-by-line instead of readlines() to handle potentially huge single lines or memory blowups
                for idx, line in enumerate(f, 1):
                    if idx >= start_line and idx <= end_line:
                        lines_to_read.append(line)
                    elif idx > end_line:
                        break
        except Exception as e:
            logger.error(f"SnippetExtractor: Error reading file {file_path}: {e}")
            return None

        if not lines_to_read:
            return None

        # Join the code lines (newlines are already preserved in string lines)
        code = "".join(lines_to_read)

        # Make sure we got something substantial
        if not code.strip():
            return None

        return {
            "start_line": start_line,
            "end_line": min(start_line + len(lines_to_read) - 1, end_line),
            "code": code,
        }
