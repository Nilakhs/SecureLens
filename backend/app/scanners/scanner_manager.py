"""
scanner_manager.py — The orchestration heart of SecureLens.

The ScannerManager is the ONLY component that knows about individual scanners.
Everything above it (API routes, ProjectAnalyzer) only ever calls:

    ScannerManager.run(project_path, scan_id)

To add a new scanner in the future:
    1. Create the scanner file (e.g. gitleaks_scanner.py)
    2. Create the parser in parser.py
    3. Register it in SCANNERS below
    Nothing else changes.
"""

import os
from app.scanners.semgrep_scanner import SemgrepScanner
from app.scanners.bandit_scanner import BanditScanner
from app.scanners.parser import SemgrepParser, BanditParser


# ---------------------------------------------------------------------------
# Scanner Registry
# ---------------------------------------------------------------------------
# Each entry: (scanner_name, scanner_class, parser_class)
# To add a new scanner, just append a tuple here.
SCANNERS = [
    ("semgrep", SemgrepScanner, SemgrepParser),
    ("bandit",  BanditScanner,  BanditParser),
]

# Severity ordering (highest → lowest) for comparison
_SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def _higher_severity(a: str, b: str) -> str:
    """Return whichever severity level is higher."""
    idx_a = _SEVERITY_ORDER.index(a) if a in _SEVERITY_ORDER else len(_SEVERITY_ORDER)
    idx_b = _SEVERITY_ORDER.index(b) if b in _SEVERITY_ORDER else len(_SEVERITY_ORDER)
    return a if idx_a <= idx_b else b


def _make_dedup_key(finding: dict) -> tuple:
    """
    Create a deduplication key for a finding.
    Two findings are considered duplicates if they point to the same
    file, line number, and vulnerability category.
    """
    return (
        finding.get("file", "").lower(),
        finding.get("line", 0),
        finding.get("category", "").lower().strip(),
    )


def _merge_findings(all_findings: list) -> list:
    """
    Merge duplicate findings from different scanners into single entries.

    When two scanners report the same issue (same file + line + category):
    - The 'scanner' field becomes a list of scanner names
    - The highest severity wins
    - The longest description is kept (usually more informative)
    - CWE, OWASP, and references are union-merged

    Returns:
        Deduplicated list of Finding dicts, sorted by severity (high → low).
    """
    merged = {}  # key → finding

    for finding in all_findings:
        key = _make_dedup_key(finding)

        if key not in merged:
            # First time seeing this issue — store it with scanner as a list
            finding_copy = dict(finding)
            finding_copy["detected_by"] = [finding["scanner"]]
            merged[key] = finding_copy
        else:
            existing = merged[key]

            # Merge scanner list
            scanner_name = finding["scanner"]
            if scanner_name not in existing["detected_by"]:
                existing["detected_by"].append(scanner_name)

            # Keep highest severity
            existing["severity"] = _higher_severity(
                existing["severity"], finding["severity"]
            )

            # Keep longest description
            if len(finding.get("description", "")) > len(existing.get("description", "")):
                existing["description"] = finding["description"]

            # Union-merge metadata lists
            for field in ("cwe", "owasp", "references"):
                existing[field] = list(
                    dict.fromkeys(existing.get(field, []) + finding.get(field, []))
                )

    result = list(merged.values())

    # Sort by severity (CRITICAL first, INFO last), then by file + line
    def sort_key(f):
        sev_idx = _SEVERITY_ORDER.index(f["severity"]) if f["severity"] in _SEVERITY_ORDER else 99
        return (sev_idx, f.get("file", ""), f.get("line", 0))

    result.sort(key=sort_key)
    return result


def _compute_summary(findings: list, scanners_status: dict) -> dict:
    """
    Compute summary statistics from the merged findings list.
    """
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

    for finding in findings:
        sev = finding.get("severity", "INFO")
        if sev in counts:
            counts[sev] += 1

    return {
        "total_findings": len(findings),
        "critical":       counts["CRITICAL"],
        "high":           counts["HIGH"],
        "medium":         counts["MEDIUM"],
        "low":            counts["LOW"],
        "info":           counts["INFO"],
        "scanners_run":   list(scanners_status.keys()),
        "scanners_status": scanners_status,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ScannerManager:
    """
    Orchestrates all registered scanners, normalizes findings, merges
    duplicates, and returns a unified report.
    """

    @staticmethod
    def run(project_path: str, scan_id: str) -> dict:
        """
        Run all registered scanners against the given project path.

        Args:
            project_path: Path to the extracted project directory.
            scan_id:      Unique identifier for this scan (for traceability).

        Returns:
            dict with keys:
                "scan_id"          → str
                "scanners_status"  → dict mapping scanner name → status string
                "summary"          → dict with severity counts + scanner info
                "findings"         → list of merged, normalized Finding dicts
        """
        all_findings = []
        scanners_status = {}

        for scanner_name, scanner_class, parser_class in SCANNERS:
            # --- Run the scanner ---
            scan_result = scanner_class.scan(project_path)
            status = scan_result.get("status", "error")
            scanners_status[scanner_name] = status

            if status != "success":
                # Scanner failed or timed out — skip, continue with others
                continue

            # --- Parse raw output into normalized findings ---
            raw = scan_result.get("raw", {})
            findings = parser_class.parse(raw)

            all_findings.extend(findings)

        # --- Merge duplicates across scanners ---
        merged = _merge_findings(all_findings)

        # --- Compute summary statistics ---
        summary = _compute_summary(merged, scanners_status)

        return {
            "scan_id":  scan_id,
            "summary":  summary,
            "findings": merged,
        }
