"""
parser.py — Normalizes raw scanner output into the SecureLens Finding model.

Each scanner produces its own JSON format. This module converts them all into
a single, consistent structure so the rest of the application never needs to
know which scanner produced a given finding.

SecureLens Finding Model:
{
    "scanner":        str,   # "semgrep" | "bandit"
    "severity":       str,   # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
    "title":          str,   # short human-readable rule name
    "description":    str,   # full explanation of the issue
    "file":           str,   # relative file path
    "line":           int,   # line number
    "rule_id":        str,   # original rule/check ID from the scanner
    "category":       str,   # e.g. "Command Injection", "Hardcoded Password"
    "cwe":            list,  # e.g. ["CWE-78"]
    "owasp":          list,  # e.g. ["A03:2021"]
    "references":     list,  # list of URLs
    "recommendation": str,   # placeholder for future AI-generated fix
}
"""

import os


# ---------------------------------------------------------------------------
# Severity normalization
# ---------------------------------------------------------------------------

_SEMGREP_SEVERITY_MAP = {
    "critical": "CRITICAL",
    "error":    "HIGH",
    "warning":  "MEDIUM",
    "info":     "LOW",
}

_BANDIT_SEVERITY_MAP = {
    "critical": "CRITICAL",
    "high":     "HIGH",
    "medium":   "MEDIUM",
    "low":      "LOW",
    "undefined": "INFO",
}


def _normalize_semgrep_severity(raw_severity: str) -> str:
    return _SEMGREP_SEVERITY_MAP.get(raw_severity.lower(), "INFO")


def _normalize_bandit_severity(raw_severity: str) -> str:
    return _BANDIT_SEVERITY_MAP.get(raw_severity.lower(), "INFO")


def _human_title(rule_id: str) -> str:
    """Convert a dotted rule ID like 'python.lang.security.subprocess-shell-true'
    into a readable title like 'Subprocess Shell True'."""
    last_segment = rule_id.split(".")[-1].split("/")[-1]
    return last_segment.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Semgrep Parser
# ---------------------------------------------------------------------------

class SemgrepParser:
    """
    Parses raw Semgrep JSON output into a list of normalized Finding dicts.
    """

    @staticmethod
    def parse(raw: dict) -> list:
        """
        Args:
            raw: Parsed JSON dict from SemgrepScanner.

        Returns:
            List of normalized Finding dicts. Empty list if no results.
        """
        findings = []
        results = raw.get("results", [])

        for result in results:
            try:
                extra = result.get("extra", {})
                metadata = extra.get("metadata", {})

                severity_raw = extra.get("severity", "info")
                severity = _normalize_semgrep_severity(severity_raw)

                rule_id = result.get("check_id", "unknown")
                title = _human_title(rule_id)

                # Vulnerability class / category
                vuln_classes = metadata.get("vulnerability_class", [])
                category = vuln_classes[0] if vuln_classes else _human_title(rule_id)

                # CWE can be a list of strings or a single string
                cwe_raw = metadata.get("cwe", [])
                cwe = [cwe_raw] if isinstance(cwe_raw, str) else cwe_raw

                # OWASP same pattern
                owasp_raw = metadata.get("owasp", [])
                owasp = [owasp_raw] if isinstance(owasp_raw, str) else owasp_raw

                references = metadata.get("references", [])

                finding = {
                    "scanner": "semgrep",
                    "severity": severity,
                    "title": title,
                    "description": extra.get("message", "No description available."),
                    "file": result.get("path", "unknown"),
                    "line": result.get("start", {}).get("line", 0),
                    "rule_id": rule_id,
                    "category": category,
                    "cwe": cwe,
                    "owasp": owasp,
                    "references": references,
                    "recommendation": "Review the references above for remediation guidance.",
                }

                findings.append(finding)

            except Exception:
                # Skip malformed individual findings — don't crash the whole scan
                continue

        return findings


# ---------------------------------------------------------------------------
# Bandit Parser
# ---------------------------------------------------------------------------

class BanditParser:
    """
    Parses raw Bandit JSON output into a list of normalized Finding dicts.
    """

    @staticmethod
    def parse(raw: dict) -> list:
        """
        Args:
            raw: Parsed JSON dict from BanditScanner.

        Returns:
            List of normalized Finding dicts. Empty list if no results.
        """
        findings = []
        results = raw.get("results", [])

        for result in results:
            try:
                severity_raw = result.get("issue_severity", "low")
                severity = _normalize_bandit_severity(severity_raw)

                rule_id = result.get("test_id", "unknown")
                test_name = result.get("test_name", rule_id)
                title = test_name.replace("_", " ").title()

                # Bandit provides CWE as an object: {"id": 78, "link": "..."}
                cwe_obj = result.get("issue_cwe", {})
                cwe_id = cwe_obj.get("id")
                cwe = [f"CWE-{cwe_id}"] if cwe_id else []

                # Build category from test name (cleaned up)
                category = title

                # Bandit provides a reference URL
                more_info = result.get("more_info", "")
                references = [more_info] if more_info else []

                finding = {
                    "scanner": "bandit",
                    "severity": severity,
                    "title": title,
                    "description": result.get("issue_text", "No description available."),
                    "file": result.get("filename", "unknown"),
                    "line": result.get("line_number", 0),
                    "rule_id": rule_id,
                    "category": category,
                    "cwe": cwe,
                    "owasp": [],  # Bandit does not provide OWASP tags directly
                    "references": references,
                    "recommendation": "Review the Bandit documentation link above for remediation guidance.",
                }

                findings.append(finding)

            except Exception:
                # Skip malformed individual findings
                continue

        return findings
