import os
import sys
import json
import hashlib
import logging
import tempfile
import shutil
import subprocess
from sqlalchemy.orm import Session

from app.ai.snippet_extractor import SnippetExtractor
from app.ai.llm_client import LLMInvalidResponseError
from app.remediation.patch_generator import PatchGenerator
from app.remediation.patch_validator import PatchValidator
from app.remediation.diff_generator import DiffGenerator
from app.models.remediation import Remediation

logger = logging.getLogger(__name__)


# ── In-memory remediation cache ──────────────────────────────────────────────

class RemediationCache:
    _store: dict = {}
    MAX_ENTRIES = 300

    @classmethod
    def make_key(cls, finding: dict, snippet: dict | None) -> str:
        parts = [
            finding.get("category", "").lower(),
            finding.get("rule_id", "").lower(),
            finding.get("file", "").replace("\\", "/").lower(),
            str(finding.get("line", 0)),
        ]
        # IMPORTANT: include exact code so different versions of the same file
        # don't share cached fixes
        if snippet and snippet.get("code"):
            parts.append(snippet["code"])
        raw = "|".join(parts)
        return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()

    @classmethod
    def get(cls, key: str) -> dict | None:
        return cls._store.get(key)

    @classmethod
    def set(cls, key: str, value: dict) -> None:
        if len(cls._store) >= cls.MAX_ENTRIES:
            first_key = next(iter(cls._store))
            cls._store.pop(first_key, None)
        cls._store[key] = dict(value)


# ── Path helper (same logic as explanation_service) ──────────────────────────

def _resolve_file_path(project_path: str | None, finding_file: str) -> str | None:
    if not project_path or not finding_file:
        return None
    proj  = os.path.normpath(project_path)
    ffile = os.path.normpath(finding_file)
    if os.path.isabs(ffile):
        return ffile
    if ffile.startswith(proj + os.sep) or ffile == proj:
        return ffile
    return os.path.join(proj, ffile)


# ── Fix Verification (stretch goal) ──────────────────────────────────────────

def _verify_fix(
    finding:       dict,
    file_path:     str,
    snippet:       dict,
    fixed_code:    str,
) -> str:
    """
    Create a temporary patched copy of the file and re-run Semgrep to check
    whether the original finding still fires.

    Returns: "VERIFIED" | "FAILED" | "UNVERIFIED"
    """
    rule_id = finding.get("rule_id", "")
    if not rule_id or not file_path or not os.path.isfile(file_path):
        return "UNVERIFIED"

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            original_lines = f.readlines()
    except Exception as e:
        logger.error(f"_verify_fix: Could not read original file: {e}")
        return "UNVERIFIED"

    # Build patched file: replace the snippet lines with fixed_code
    start_idx = max(0, snippet["start_line"] - 1)
    end_idx   = min(len(original_lines), snippet["end_line"])

    fixed_lines = (fixed_code + "\n").splitlines(keepends=True)
    patched_lines = original_lines[:start_idx] + fixed_lines + original_lines[end_idx:]

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Copy the file with the fix applied
            filename = os.path.basename(file_path)
            tmp_file = os.path.join(tmp_dir, filename)

            with open(tmp_file, "w", encoding="utf-8") as f:
                f.writelines(patched_lines)

            # Locate semgrep executable from the current Python environment
            semgrep_exe = os.path.join(os.path.dirname(sys.executable), "semgrep")
            if not os.path.isfile(semgrep_exe):
                semgrep_exe = os.path.join(os.path.dirname(sys.executable), "semgrep.exe")
            if not os.path.isfile(semgrep_exe):
                semgrep_exe = "semgrep"  # fallback: hope it's in PATH

            result = subprocess.run(
                [
                    semgrep_exe,
                    "--config", "auto",
                    "--json",
                    "--quiet",
                    tmp_file,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )

            if result.returncode not in (0, 1):
                logger.warning(f"_verify_fix: Semgrep exited with code {result.returncode}")
                return "UNVERIFIED"

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning("_verify_fix: Could not parse Semgrep JSON output.")
                return "UNVERIFIED"

            results = data.get("results", [])
            # Check if the original rule still fires in the patched file
            still_fires = any(
                r.get("check_id", "").endswith(rule_id.split(".")[-1]) or
                rule_id in r.get("check_id", "")
                for r in results
            )

            if still_fires:
                logger.info(f"_verify_fix: Rule {rule_id} still fires after fix → FAILED")
                return "FAILED"
            else:
                logger.info(f"_verify_fix: Rule {rule_id} no longer fires after fix → VERIFIED")
                return "VERIFIED"

    except subprocess.TimeoutExpired:
        logger.warning("_verify_fix: Semgrep timed out during verification.")
        return "UNVERIFIED"
    except Exception as e:
        logger.error(f"_verify_fix: Unexpected error: {e}")
        return "UNVERIFIED"


# ── Main Service ─────────────────────────────────────────────────────────────

class RemediationService:
    """
    Orchestrates: snippet extraction → cache → patch generation → validation
    → diff → verification → return.
    """

    REQUIRED_KEYS = {"fixed_code", "explanation", "changes", "limitations"}

    @classmethod
    def fix(cls, finding: dict, project_path: str | None = None, db: Session | None = None) -> dict:
        """
        Generate a verified, validated AI-proposed security fix.
        Utilizes both in-memory cache and PostgreSQL database persistence.

        Args:
            finding:      Normalized finding dict.
            project_path: Path to extracted project on disk (optional).
            db:           Optional database session.

        Returns:
            dict matching RemediationFix schema.

        Raises:
            LLMError subclasses on AI failure.
        """
        finding_id = finding.get("id")

        # 1. Resolve file path
        file_path = _resolve_file_path(project_path, finding.get("file", ""))

        # 2. Extract code snippet
        line_number = finding.get("line", 0)
        snippet = None
        if file_path and line_number > 0:
            try:
                snippet = SnippetExtractor.extract(file_path, line_number)
            except Exception as e:
                logger.error(f"RemediationService: Snippet extraction failed: {e}")

        original_code = snippet["code"] if snippet else ""

        # 3. Check in-memory Cache first
        cache_key = RemediationCache.make_key(finding, snippet)
        cached = RemediationCache.get(cache_key)
        if cached:
            logger.info("RemediationService: In-memory cache hit.")
            result = dict(cached)
            result["cached"] = True
            return result

        # 4. Check Database if finding_id is present
        if db and finding_id:
            try:
                db_remediation = db.query(Remediation).filter(Remediation.finding_id == finding_id).first()
                if db_remediation:
                    logger.info(f"RemediationService: DB hit for finding_id {finding_id}. Loading into memory cache.")
                    
                    # Convert stored bullet points list back from DB format if list was saved as JSON
                    # Wait, in SQLAlchemy remediations table, changes is not stored, only explanation/original/fixed/diff.
                    # Wait, we can construct standard changes from explanation if needed, or if we look at DB columns:
                    # original_code, fixed_code, explanation, diff, syntax_valid, verification_status.
                    # Let's see: we can mock changes from explanation or retrieve it
                    result = {
                        "original_code":       db_remediation.original_code,
                        "fixed_code":          db_remediation.fixed_code,
                        "explanation":         db_remediation.explanation,
                        "changes":             ["Security fix applied from database record."], # fallback
                        "limitations":         "Audit record from previous generation.",
                        "diff":                db_remediation.diff,
                        "syntax_valid":        db_remediation.syntax_valid,
                        "language":            "unknown",  # fallback
                        "verification_status": db_remediation.verification_status,
                        "cached":              True,
                        "model_used":          db_remediation.model,
                    }
                    RemediationCache.set(cache_key, result)
                    return result
            except Exception as db_err:
                logger.error(f"RemediationService: Database query failed: {db_err}")

        # 5. Generate patch via AI
        raw = PatchGenerator.generate(finding, snippet)

        # 6. Validate response structure
        if not isinstance(raw, dict):
            raise LLMInvalidResponseError("Remediation AI response was not a JSON object.")
        missing = cls.REQUIRED_KEYS - raw.keys()
        if missing:
            raise LLMInvalidResponseError(f"Remediation response missing fields: {', '.join(missing)}")

        fixed_code  = str(raw.get("fixed_code", "")).strip()
        explanation = str(raw.get("explanation", "")).strip()
        changes_raw = raw.get("changes", [])
        limitations = str(raw.get("limitations", "")).strip()

        # Normalize changes to a list of strings
        if isinstance(changes_raw, list):
            changes = [str(c).strip() for c in changes_raw if str(c).strip()]
        else:
            changes = [str(changes_raw).strip()]

        # 7. Syntax validation
        syntax_valid, language = PatchValidator.validate(fixed_code, finding.get("file"))

        # 8. Generate unified diff
        fname = os.path.basename(finding.get("file", "file"))
        diff  = DiffGenerator.generate(original_code, fixed_code, fname)

        # 9. Stretch: re-scan verification
        verification_status = "UNVERIFIED"
        if syntax_valid and file_path and snippet:
            verification_status = _verify_fix(finding, file_path, snippet, fixed_code)

        model_name = os.getenv("AI_MODEL", "gemini-2.5-flash")

        result = {
            "original_code":       original_code,
            "fixed_code":          fixed_code,
            "explanation":         explanation,
            "changes":             changes,
            "limitations":         limitations,
            "diff":                diff,
            "syntax_valid":        syntax_valid,
            "language":            language,
            "verification_status": verification_status,
            "cached":              False,
            "model_used":          model_name,
        }

        # 10. Save to Database if db and finding_id are available
        if db and finding_id:
            try:
                db_remediation = Remediation(
                    finding_id=finding_id,
                    model=model_name,
                    original_code=original_code,
                    fixed_code=fixed_code,
                    explanation=explanation,
                    diff=diff,
                    syntax_valid=syntax_valid,
                    verification_status=verification_status
                )
                db.add(db_remediation)
                db.commit()
                logger.info(f"RemediationService: Saved remediation for finding_id {finding_id} to DB.")
            except Exception as db_save_err:
                db.rollback()
                logger.error(f"RemediationService: Failed to save remediation to database: {db_save_err}")

        # 11. Save to in-memory Cache
        RemediationCache.set(cache_key, result)
        return result
