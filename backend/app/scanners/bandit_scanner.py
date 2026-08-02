import subprocess
import json
import sys
import os


def _bandit_executable() -> str:
    """
    Resolve the bandit executable from the same virtual environment
    as the running Python interpreter, so it works even when the
    venv is not activated on the system PATH.
    """
    scripts_dir = os.path.dirname(sys.executable)
    candidates = [
        os.path.join(scripts_dir, "bandit.exe"),  # Windows venv
        os.path.join(scripts_dir, "bandit"),       # Unix venv / system
        "bandit",                                   # fallback: rely on PATH
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return "bandit"


class BanditScanner:
    """
    Runs Bandit on a project directory and returns the raw JSON output.
    Bandit specializes in Python security issues (eval, exec, shell injection,
    hardcoded passwords, weak crypto, pickle, etc.).
    Does NOT parse or normalize — that is the responsibility of parser.py.
    """

    TIMEOUT_SECONDS = 120

    @staticmethod
    def scan(project_path: str) -> dict:
        """
        Execute Bandit against the given project path.

        Args:
            project_path: Absolute or relative path to the extracted project directory.

        Returns:
            dict with keys:
                "status"  → "success" | "error" | "timeout"
                "raw"     → parsed JSON dict (only on success)
                "message" → error description (only on error/timeout)
        """
        try:
            result = subprocess.run(
                [
                    _bandit_executable(),
                    "-r",          # recursive
                    project_path,
                    "-f", "json",  # JSON output format
                    "-q",          # quiet — suppress progress output
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=BanditScanner.TIMEOUT_SECONDS,
            )

            # Bandit exits with code 1 when issues are found — that is not an error.
            # It exits with code 2 for usage errors.
            if result.returncode == 2:
                return {
                    "status": "error",
                    "message": f"Bandit usage error: {result.stderr.strip()}",
                }

            # If stdout is empty (no Python files found), return empty results
            if not result.stdout.strip():
                return {
                    "status": "success",
                    "raw": {"results": [], "metrics": {}},
                }

            raw = json.loads(result.stdout)
            return {"status": "success", "raw": raw}

        except FileNotFoundError:
            return {
                "status": "error",
                "message": "Bandit is not installed or not found on PATH.",
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": f"Bandit timed out after {BanditScanner.TIMEOUT_SECONDS} seconds.",
            }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse Bandit JSON output: {e}",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Bandit scanner encountered an unexpected error: {e}",
            }
