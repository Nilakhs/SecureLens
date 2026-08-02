import subprocess
import json
import sys
import os


def _semgrep_executable() -> str:
    """
    Resolve the semgrep executable, checking the venv Scripts directory
    first before falling back to the system PATH.
    """
    scripts_dir = os.path.dirname(sys.executable)
    candidates = [
        os.path.join(scripts_dir, "semgrep.exe"),  # Windows venv
        os.path.join(scripts_dir, "semgrep"),       # Unix venv
        "semgrep",                                   # system PATH fallback
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return "semgrep"


class SemgrepScanner:
    """
    Runs Semgrep on a project directory and returns the raw JSON output.
    Does NOT parse or normalize — that is the responsibility of parser.py.
    """

    TIMEOUT_SECONDS = 120

    @staticmethod
    def scan(project_path: str) -> dict:
        """
        Execute Semgrep against the given project path.

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
                    _semgrep_executable(),
                    "--config=p/security-audit",
                    "--json",
                    "--no-git-ignore",
                    project_path,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=SemgrepScanner.TIMEOUT_SECONDS,
            )

            # Semgrep exits with code 1 when findings are present — that is not an error.
            # It exits with code 2 or higher for actual errors.
            if result.returncode not in (0, 1):
                return {
                    "status": "error",
                    "message": f"Semgrep exited with code {result.returncode}: {result.stderr.strip()}",
                }

            raw = json.loads(result.stdout)
            return {"status": "success", "raw": raw}

        except FileNotFoundError:
            return {
                "status": "error",
                "message": "Semgrep is not installed or not found on PATH.",
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": f"Semgrep timed out after {SemgrepScanner.TIMEOUT_SECONDS} seconds.",
            }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse Semgrep JSON output: {e}",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Semgrep scanner encountered an unexpected error: {e}",
            }
